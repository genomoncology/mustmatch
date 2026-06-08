use std::collections::{HashMap, HashSet};
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

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ConfigKey {
    pub(crate) root: PathBuf,
    pub(crate) source: Option<&'static str>,
}

struct ContextScope {
    name: String,
    settings: ContextSettings,
    tokens: HashMap<&'static str, String>,
}

struct HookScope {
    cwd: PathBuf,
    env: HashMap<String, String>,
    tokens: HashMap<&'static str, String>,
}

pub(crate) struct ContextRegistry {
    root: PathBuf,
    source: Option<&'static str>,
    config: Value,
    cache: HashMap<String, ContextScope>,
    remaining_uses: HashMap<String, usize>,
    touched: HashSet<String>,
    suite_scope: Option<HookScope>,
    file_scope: Option<HookScope>,
    tempdirs: Vec<TempDir>,
}

impl ContextRegistry {
    pub(crate) fn new(path: &Path) -> Result<Self, String> {
        let (config_path, source) = find_config(path);
        let root = config_path
            .as_deref()
            .map(effective_parent)
            .unwrap_or_else(|| effective_parent(path));
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
            remaining_uses: HashMap::new(),
            touched: HashSet::new(),
            suite_scope: None,
            file_scope: None,
            tempdirs: Vec::new(),
        })
    }

    pub(crate) fn config_key(&self) -> ConfigKey {
        ConfigKey {
            root: self.root.clone(),
            source: self.source,
        }
    }

    pub(crate) fn register_context_use(&mut self, name: &str, cache_scope: Option<&str>) {
        let name = name.trim();
        if name.is_empty() {
            return;
        }
        *self
            .remaining_uses
            .entry(context_cache_key(name, cache_scope))
            .or_insert(0) += 1;
    }

    pub(crate) fn finish_case(&mut self) -> Result<(), String> {
        let touched: Vec<String> = self.touched.drain().collect();
        let mut first_error = None;
        for key in touched {
            let remaining = self.remaining_uses.entry(key.clone()).or_insert(1);
            *remaining = remaining.saturating_sub(1);
            if *remaining == 0 {
                self.remaining_uses.remove(&key);
                if let Err(err) = self.run_context_teardown(&key) {
                    first_error.get_or_insert(err);
                }
            }
        }
        result_from_first_error(first_error)
    }

    pub(crate) fn finish_all_contexts(&mut self) -> Result<(), String> {
        self.remaining_uses.clear();
        self.touched.clear();
        let mut keys: Vec<String> = self.cache.keys().cloned().collect();
        keys.sort();
        let mut first_error = None;
        for key in keys {
            if let Err(err) = self.run_context_teardown(&key) {
                first_error.get_or_insert(err);
            }
        }
        result_from_first_error(first_error)
    }

    pub(crate) fn run_suite_setup(&mut self) -> Result<(), String> {
        let config = section_config(&self.config, "suite");
        let root = self.root.clone();
        let scope = self.hook_scope(&config, &root)?;
        run_setup_with_teardown_on_failure("suite", &config, &scope)?;
        self.suite_scope = Some(scope);
        Ok(())
    }

    pub(crate) fn run_suite_teardown(&mut self) -> Result<(), String> {
        let Some(scope) = self.suite_scope.take() else {
            return Ok(());
        };
        let config = section_config(&self.config, "suite");
        run_hook_commands("suite", "teardown", &config, &scope)
    }

    pub(crate) fn run_file_setup(&mut self, default_cwd: &Path) -> Result<(), String> {
        let config = section_config(&self.config, "file");
        let scope = self.hook_scope(&config, default_cwd)?;
        run_setup_with_teardown_on_failure("file", &config, &scope)?;
        self.file_scope = Some(scope);
        Ok(())
    }

    pub(crate) fn run_file_teardown(&mut self) -> Result<(), String> {
        let Some(scope) = self.file_scope.take() else {
            return Ok(());
        };
        let config = section_config(&self.config, "file");
        run_hook_commands("file", "teardown", &config, &scope)
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
        let cache_key = context_cache_key(name, cache_scope);
        if let Some(scope) = self.cache.get(&cache_key) {
            self.touched.insert(cache_key);
            return Ok(scope.settings.clone());
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

        self.apply_env_files(&self.config, &mut env, &tokens)?;
        self.apply_env(&self.config, &mut env, &tokens);
        self.apply_path(&self.config, &mut env, &tokens);
        self.apply_env_files(config, &mut env, &tokens)?;
        self.apply_env(config, &mut env, &tokens);
        self.apply_path(config, &mut env, &tokens);
        self.check_required_env(name, config, &env)?;
        self.run_setup(name, config, &cwd, &env, &tokens)?;

        let settings = ContextSettings { cwd, env };
        self.cache.insert(
            cache_key.clone(),
            ContextScope {
                name: name.to_string(),
                settings: settings.clone(),
                tokens,
            },
        );
        self.touched.insert(cache_key);
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
        let scope = HookScope {
            cwd: cwd.to_path_buf(),
            env: env.clone(),
            tokens: tokens.clone(),
        };
        run_setup_with_teardown_on_failure(&format!("context {name:?}"), config, &scope)
    }

    fn run_context_teardown(&mut self, key: &str) -> Result<(), String> {
        let Some(scope) = self.cache.remove(key) else {
            return Ok(());
        };
        let config = self
            .config
            .get("contexts")
            .and_then(|contexts| contexts.get(&scope.name))
            .cloned()
            .unwrap_or_else(|| Value::Table(Default::default()));
        let hook = HookScope {
            cwd: scope.settings.cwd,
            env: scope.settings.env,
            tokens: scope.tokens,
        };
        run_hook_commands(
            &format!("context {:?}", scope.name),
            "teardown",
            &config,
            &hook,
        )
    }

    fn hook_scope(&mut self, config: &Value, default_cwd: &Path) -> Result<HookScope, String> {
        let tmp = TempDir::new().map_err(|err| format!("failed to create tempdir: {err}"))?;
        let tmp_path = tmp.path().to_path_buf();
        self.tempdirs.push(tmp);
        let mut env = process_env();
        let tokens = tokens(&self.root, default_cwd, &tmp_path);
        let cwd_value = config.get("cwd").and_then(Value::as_str).unwrap_or(".");
        let cwd = resolve_path(&self.root, &expand(cwd_value, &env, &tokens));

        self.apply_env_files(&self.config, &mut env, &tokens)?;
        self.apply_env(&self.config, &mut env, &tokens);
        self.apply_path(&self.config, &mut env, &tokens);
        self.apply_env_files(config, &mut env, &tokens)?;
        self.apply_env(config, &mut env, &tokens);
        self.apply_path(config, &mut env, &tokens);

        Ok(HookScope { cwd, env, tokens })
    }
}

fn run_hook_commands(
    label: &str,
    phase: &str,
    config: &Value,
    scope: &HookScope,
) -> Result<(), String> {
    let timeout_key = format!("{phase}_timeout");
    let timeout = config
        .get(&timeout_key)
        .or_else(|| config.get("timeout"))
        .and_then(Value::as_integer)
        .and_then(|value| u64::try_from(value).ok())
        .unwrap_or(120);
    for command in string_list(config.get(phase)) {
        let command = expand(&command, &scope.env, &scope.tokens);
        if command.trim().is_empty() {
            continue;
        }
        let result = run_bash(&command, &scope.cwd, &scope.env, timeout)
            .map_err(|err| format!("{label} {phase} command failed: {err}"))?;
        if result.exit_code != 0 {
            return Err(format!(
                "{label} {phase} command failed\n{}{}",
                result.stdout, result.stderr
            ));
        }
    }
    Ok(())
}

fn run_setup_with_teardown_on_failure(
    label: &str,
    config: &Value,
    scope: &HookScope,
) -> Result<(), String> {
    match run_hook_commands(label, "setup", config, scope) {
        Ok(()) => Ok(()),
        Err(setup_error) => match run_hook_commands(label, "teardown", config, scope) {
            Ok(()) => Err(setup_error),
            Err(teardown_error) => Err(format!(
                "{setup_error}\n{label} teardown after setup failure failed\n{teardown_error}"
            )),
        },
    }
}

fn section_config(config: &Value, name: &str) -> Value {
    config
        .get(name)
        .cloned()
        .unwrap_or_else(|| Value::Table(Default::default()))
}

fn context_cache_key(name: &str, cache_scope: Option<&str>) -> String {
    match cache_scope {
        Some(scope) => format!("{name}@{scope}"),
        None => name.to_string(),
    }
}

fn result_from_first_error(first_error: Option<String>) -> Result<(), String> {
    match first_error {
        Some(err) => Err(err),
        None => Ok(()),
    }
}

fn find_config(path: &Path) -> (Option<PathBuf>, Option<&'static str>) {
    let start = if path.is_dir() {
        path.to_path_buf()
    } else {
        effective_parent(path)
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

fn effective_parent(path: &Path) -> PathBuf {
    match path.parent() {
        Some(parent) if !parent.as_os_str().is_empty() => parent.to_path_buf(),
        _ => PathBuf::from("."),
    }
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
