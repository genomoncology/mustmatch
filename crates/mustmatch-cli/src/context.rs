use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use tempfile::TempDir;
use toml::Value;

use crate::process::run_bash;

#[derive(Debug, Clone)]
pub(crate) struct ContextSettings {
    pub(crate) cwd: PathBuf,
    pub(crate) env: HashMap<String, String>,
}

pub(crate) struct ContextRegistry {
    root: PathBuf,
    source: Option<&'static str>,
    config: Value,
    cache: HashMap<String, ContextSettings>,
    tempdirs: Vec<TempDir>,
}

impl ContextRegistry {
    pub(crate) fn new(path: &Path) -> Result<Self, String> {
        let (config_path, source) = find_config(path);
        let root = config_path
            .as_ref()
            .and_then(|candidate| candidate.parent().map(Path::to_path_buf))
            .unwrap_or_else(|| path.parent().unwrap_or(path).to_path_buf());
        let root = fs::canonicalize(&root).unwrap_or(root);
        let config = match (&config_path, source) {
            (Some(candidate), Some("mustmatch")) => parse_toml(candidate)?,
            (Some(candidate), Some("pyproject")) => parse_toml(candidate)?
                .get("tool")
                .and_then(|tool| tool.get("mustmatch"))
                .cloned()
                .unwrap_or(Value::Table(Default::default())),
            _ => Value::Table(Default::default()),
        };
        Ok(Self {
            root,
            source,
            config,
            cache: HashMap::new(),
            tempdirs: Vec::new(),
        })
    }

    pub(crate) fn resolve(
        &mut self,
        name: Option<&str>,
        default_cwd: &Path,
    ) -> Result<ContextSettings, String> {
        self.resolve_scoped(name, default_cwd, None)
    }

    pub(crate) fn resolve_scoped(
        &mut self,
        name: Option<&str>,
        default_cwd: &Path,
        cache_scope: Option<&str>,
    ) -> Result<ContextSettings, String> {
        let Some(name) = name.filter(|value| !value.trim().is_empty()) else {
            return Ok(self.base_settings(default_cwd));
        };
        let cache_key = match cache_scope {
            Some(scope) => format!("{name}@{scope}"),
            None => name.to_string(),
        };
        if let Some(settings) = self.cache.get(&cache_key) {
            return Ok(settings.clone());
        }

        let config = self
            .config
            .get("contexts")
            .and_then(|contexts| contexts.get(name))
            .ok_or_else(|| {
                format!(
                    "No mustmatch context named {name:?} in {}",
                    self.source.unwrap_or("config")
                )
            })?;

        let tmp = TempDir::new().map_err(|err| format!("failed to create tempdir: {err}"))?;
        let tmp_path = tmp.path().to_path_buf();
        self.tempdirs.push(tmp);
        let mut env = process_env();
        let tokens = tokens(&self.root, default_cwd, &tmp_path);

        let cwd_value = config.get("cwd").and_then(Value::as_str).unwrap_or(".");
        let cwd = resolve_path(&self.root, &expand(cwd_value, &env, &tokens));

        self.apply_env_files(config, &mut env, &tokens)?;
        self.apply_env(config, &mut env, &tokens);
        self.apply_path(config, &mut env, &tokens);
        self.check_required_env(name, config, &env)?;
        self.run_setup(name, config, &cwd, &env, &tokens)?;

        let settings = ContextSettings { cwd, env };
        self.cache.insert(cache_key, settings.clone());
        Ok(settings)
    }

    fn base_settings(&self, default_cwd: &Path) -> ContextSettings {
        let mut env = process_env();
        let tmp = default_cwd.to_path_buf();
        let tokens = tokens(&self.root, default_cwd, &tmp);
        self.apply_path(&self.config, &mut env, &tokens);
        ContextSettings {
            cwd: default_cwd.to_path_buf(),
            env,
        }
    }

    fn apply_env_files(
        &self,
        config: &Value,
        env: &mut HashMap<String, String>,
        tokens: &HashMap<&'static str, String>,
    ) -> Result<(), String> {
        for item in string_list(config.get("env_files").or_else(|| config.get("env_file"))) {
            let path = resolve_path(&self.root, &expand(&item, env, tokens));
            if !path.exists() {
                continue;
            }
            let content = fs::read_to_string(&path)
                .map_err(|err| format!("failed to read env file {}: {err}", path.display()))?;
            for raw in content.lines() {
                let line = raw.trim();
                if line.is_empty() || line.starts_with('#') {
                    continue;
                }
                if let Some((key, value)) = line.split_once('=') {
                    env.insert(
                        key.trim().to_string(),
                        value
                            .trim()
                            .trim_matches('"')
                            .trim_matches('\'')
                            .to_string(),
                    );
                }
            }
        }
        Ok(())
    }

    fn apply_env(
        &self,
        config: &Value,
        env: &mut HashMap<String, String>,
        tokens: &HashMap<&'static str, String>,
    ) {
        if let Some(table) = config.get("env").and_then(Value::as_table) {
            for (key, value) in table {
                env.insert(
                    key.to_string(),
                    expand(&value_to_string(value), env, tokens),
                );
            }
        }
    }

    fn apply_path(
        &self,
        config: &Value,
        env: &mut HashMap<String, String>,
        tokens: &HashMap<&'static str, String>,
    ) {
        let entries: Vec<String> = string_list(config.get("path"))
            .into_iter()
            .map(|item| resolve_path(&self.root, &expand(&item, env, tokens)))
            .map(|path| path.to_string_lossy().into_owned())
            .collect();
        if entries.is_empty() {
            return;
        }
        let old_path = env.get("PATH").cloned().unwrap_or_default();
        env.insert("PATH".to_string(), [entries.join(":"), old_path].join(":"));
    }

    fn check_required_env(
        &self,
        name: &str,
        config: &Value,
        env: &HashMap<String, String>,
    ) -> Result<(), String> {
        let missing: Vec<String> = string_list(config.get("required_env"))
            .into_iter()
            .filter(|key| env.get(key).map(String::is_empty).unwrap_or(true))
            .collect();
        if missing.is_empty() {
            Ok(())
        } else {
            Err(format!(
                "context {name:?} requires environment values: {}",
                missing.join(", ")
            ))
        }
    }

    fn run_setup(
        &self,
        name: &str,
        config: &Value,
        cwd: &Path,
        env: &HashMap<String, String>,
        tokens: &HashMap<&'static str, String>,
    ) -> Result<(), String> {
        let timeout = config
            .get("setup_timeout")
            .and_then(Value::as_integer)
            .and_then(|value| u64::try_from(value).ok())
            .unwrap_or(120);
        for command in string_list(config.get("setup")) {
            let command = expand(&command, env, tokens);
            if command.trim().is_empty() {
                continue;
            }
            let result = run_bash(&command, cwd, env, timeout)
                .map_err(|err| format!("context {name:?} setup command failed: {err}"))?;
            if result.exit_code != 0 {
                return Err(format!(
                    "context {name:?} setup command failed\n{}{}",
                    result.stdout, result.stderr
                ));
            }
        }
        Ok(())
    }
}

fn find_config(path: &Path) -> (Option<PathBuf>, Option<&'static str>) {
    let start = if path.is_dir() {
        path.to_path_buf()
    } else {
        path.parent().unwrap_or(path).to_path_buf()
    };
    for dir in start.ancestors() {
        let mustmatch = dir.join("mustmatch.toml");
        if mustmatch.exists() {
            return (Some(mustmatch), Some("mustmatch"));
        }
    }
    for dir in start.ancestors() {
        let pyproject = dir.join("pyproject.toml");
        if pyproject.exists() {
            return (Some(pyproject), Some("pyproject"));
        }
    }
    (None, None)
}

fn parse_toml(path: &Path) -> Result<Value, String> {
    let content = fs::read_to_string(path)
        .map_err(|err| format!("failed to read config {}: {err}", path.display()))?;
    content
        .parse::<Value>()
        .map_err(|err| format!("failed to parse config {}: {err}", path.display()))
}

fn process_env() -> HashMap<String, String> {
    env::vars().collect()
}

fn tokens(root: &Path, cwd: &Path, tmp: &Path) -> HashMap<&'static str, String> {
    HashMap::from([
        ("root", root.to_string_lossy().into_owned()),
        ("cwd", cwd.to_string_lossy().into_owned()),
        ("tmp", tmp.to_string_lossy().into_owned()),
    ])
}

fn expand(
    value: &str,
    env: &HashMap<String, String>,
    tokens: &HashMap<&'static str, String>,
) -> String {
    let mut out = value.to_string();
    for (key, replacement) in tokens {
        out = out.replace(&format!("{{{key}}}"), replacement);
    }
    expand_env(&out, env)
}

fn expand_env(value: &str, env: &HashMap<String, String>) -> String {
    let mut out = String::new();
    let mut rest = value;
    while let Some(start) = rest.find("${") {
        out.push_str(&rest[..start]);
        let after = &rest[start + 2..];
        let Some(end) = after.find('}') else {
            out.push_str(&rest[start..]);
            return out;
        };
        let key = &after[..end];
        out.push_str(env.get(key).map(String::as_str).unwrap_or(""));
        rest = &after[end + 1..];
    }
    out.push_str(rest);
    out
}

fn resolve_path(root: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        path
    } else {
        root.join(path)
    }
}

fn string_list(value: Option<&Value>) -> Vec<String> {
    match value {
        Some(Value::String(item)) => vec![item.to_string()],
        Some(Value::Array(items)) => items
            .iter()
            .filter_map(Value::as_str)
            .map(str::to_string)
            .collect(),
        _ => Vec::new(),
    }
}

fn value_to_string(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_string)
        .unwrap_or_else(|| value.to_string())
}
