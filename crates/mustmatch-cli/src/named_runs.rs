use std::collections::HashMap;
use std::path::Path;

use mustmatch_core::{Block, TableRowData};
use serde_json::Value;

use crate::context::ContextRegistry;
use crate::process::{ProcessResult, run_bash};

#[derive(Default)]
pub(crate) struct NamedRuns {
    blocks: HashMap<String, Block>,
    results: HashMap<String, ProcessResult>,
    active: Vec<String>,
}

impl NamedRuns {
    pub(crate) fn new(blocks: &[Block]) -> Self {
        let mut runs = Self::default();
        for block in blocks {
            if is_run_block(block)
                && let Some(ident) = block_id(block)
            {
                runs.blocks.insert(ident, block.clone());
            }
        }
        runs
    }

    pub(crate) fn has(&self, ident: &str) -> bool {
        self.blocks.contains_key(ident)
    }

    pub(crate) fn block(&self, ident: &str) -> Option<&Block> {
        self.blocks.get(ident)
    }

    pub(crate) fn run(
        &mut self,
        ident: &str,
        contexts: &mut ContextRegistry,
        default_cwd: &Path,
        default_timeout: u64,
    ) -> Result<ProcessResult, String> {
        self.run_with_row(ident, None, contexts, default_cwd, default_timeout)
    }

    pub(crate) fn run_with_row(
        &mut self,
        ident: &str,
        row: Option<(&str, &TableRowData)>,
        contexts: &mut ContextRegistry,
        default_cwd: &Path,
        default_timeout: u64,
    ) -> Result<ProcessResult, String> {
        let key = cache_key(ident, row.map(|(key, _)| key));
        if let Some(result) = self.results.get(&key) {
            return Ok(result.clone());
        }
        let block = self
            .blocks
            .get(ident)
            .cloned()
            .ok_or_else(|| format!("unknown run id {ident:?}"))?;
        if let Some(position) = self.active.iter().position(|item| item == &key) {
            let mut cycle = self.active[position..].to_vec();
            cycle.push(key.clone());
            return Err(format!("cyclic run dependency: {}", cycle.join(" -> ")));
        }

        self.active.push(key.clone());
        let outcome = (|| -> Result<ProcessResult, String> {
            for dependency in uses(&block) {
                self.run(&dependency, contexts, default_cwd, default_timeout)?;
            }

            let context_name = directive(&block, "context");
            let settings = contexts.resolve_scoped(
                context_name.as_deref(),
                default_cwd,
                row.map(|(key, _)| key),
            )?;
            let content = self.substitute_with_row(
                &block.content,
                row.map(|(_, row)| row),
                contexts,
                default_cwd,
                default_timeout,
            )?;
            let timeout = timeout_for(&block, default_timeout);
            let result = run_bash(&content, &settings.cwd, &settings.env, timeout)
                .map_err(|err| format!("run {ident:?} failed to start: {err}"))?;
            if result.timed_out {
                return Err(format!("run {ident:?} timed out after {timeout} seconds"));
            }
            let expected = expected_exit(&block)?;
            let stream = selected_stream(&block)?;
            if result.exit_code != expected {
                return Err(format!(
                    "run {ident:?} expected exit {expected}, actual exit {}, selected stream {stream}",
                    result.exit_code
                ));
            }
            self.results.insert(key, result.clone());
            Ok(result)
        })();
        self.active.pop();
        outcome
    }

    pub(crate) fn substitute(
        &mut self,
        text: &str,
        contexts: &mut ContextRegistry,
        default_cwd: &Path,
        default_timeout: u64,
    ) -> Result<String, String> {
        self.substitute_with_row(text, None, contexts, default_cwd, default_timeout)
    }

    pub(crate) fn substitute_with_row(
        &mut self,
        text: &str,
        row: Option<&TableRowData>,
        contexts: &mut ContextRegistry,
        default_cwd: &Path,
        default_timeout: u64,
    ) -> Result<String, String> {
        let mut out = String::new();
        let mut rest = text;
        while let Some(start) = rest.find("{{") {
            out.push_str(&rest[..start]);
            let after = &rest[start + 2..];
            let Some(end) = after.find("}}") else {
                out.push_str(&rest[start..]);
                return Ok(out);
            };
            let expr = after[..end].trim();
            out.push_str(&self.lookup(expr, row, contexts, default_cwd, default_timeout)?);
            rest = &after[end + 2..];
        }
        out.push_str(rest);
        Ok(out)
    }

    fn lookup(
        &mut self,
        expr: &str,
        row: Option<&TableRowData>,
        contexts: &mut ContextRegistry,
        default_cwd: &Path,
        default_timeout: u64,
    ) -> Result<String, String> {
        let parts: Vec<&str> = expr.split('.').collect();
        if parts.len() < 2 {
            if let Some(row) = row {
                let value = row
                    .get(expr)
                    .ok_or_else(|| format!("unknown row column {expr:?}"))?;
                return Ok(render_value(&value));
            }
            return Err(format!("template {{{{{expr}}}}} must reference run.field"));
        }
        let result = self.run(parts[0], contexts, default_cwd, default_timeout)?;
        let json: Value = serde_json::from_str(&result.stdout)
            .map_err(|err| format!("run {:?} did not produce JSON stdout: {err}", parts[0]))?;
        let value = json_path(&json, &parts[1..])?;
        Ok(render_value(value))
    }
}

pub(crate) fn render_value(value: &Value) -> String {
    match value {
        Value::String(item) => item.clone(),
        _ => value.to_string(),
    }
}

pub(crate) fn is_run_block(block: &Block) -> bool {
    block.language == "bash"
        && (block.directives.contains_key("run") || block.directives.contains_key("mustmatch-run"))
}

pub(crate) fn block_id(block: &Block) -> Option<String> {
    block
        .directives
        .get("id")
        .filter(|value| !value.is_empty())
        .cloned()
        .or_else(|| block.name.as_ref().map(|value| normalize_lookup(value)))
}

pub(crate) fn expect_target(block: &Block) -> Option<&str> {
    block
        .directives
        .get("expect")
        .or_else(|| block.directives.get("for"))
        .map(String::as_str)
}

pub(crate) fn is_output_block(block: &Block) -> bool {
    block.directives.contains_key("expect")
        || block.directives.contains_key("for")
        || block.directives.contains_key("mustmatch-output")
        || block.directives.contains_key("output")
}

pub(crate) fn expected_exit(block: &Block) -> Result<i32, String> {
    let key = if block.directives.contains_key("exit_code") {
        "exit_code"
    } else {
        "exit"
    };
    let Some(value) = block.directives.get(key) else {
        return Ok(0);
    };
    value
        .parse::<i32>()
        .map_err(|_| format!("exit directive {key} must be an integer, got {value:?}"))
}

pub(crate) fn selected_stream(block: &Block) -> Result<&str, String> {
    let stream = block
        .directives
        .get("stream")
        .map(String::as_str)
        .unwrap_or("stdout");
    if stream == "stdout" || stream == "stderr" {
        Ok(stream)
    } else {
        Err(format!(
            "stream directive must be stdout or stderr, got {stream:?}"
        ))
    }
}

pub(crate) fn result_stream<'a>(result: &'a ProcessResult, stream: &str) -> &'a str {
    if stream == "stderr" {
        &result.stderr
    } else {
        &result.stdout
    }
}

pub(crate) fn timeout_for(block: &Block, default_timeout: u64) -> u64 {
    block
        .directives
        .get("timeout")
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(default_timeout)
}

fn directive(block: &Block, key: &str) -> Option<String> {
    block
        .directives
        .get(key)
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
}

fn uses(block: &Block) -> Vec<String> {
    block
        .directives
        .get("uses")
        .map(|value| {
            value
                .split([',', ' '])
                .filter(|item| !item.trim().is_empty())
                .map(|item| item.trim().to_string())
                .collect()
        })
        .unwrap_or_default()
}

pub(crate) fn normalize_lookup(value: &str) -> String {
    let mut normalized = String::new();
    let mut prev_underscore = false;
    for ch in value.to_lowercase().chars() {
        if ch.is_ascii_alphanumeric() {
            normalized.push(ch);
            prev_underscore = false;
        } else if !prev_underscore {
            normalized.push('_');
            prev_underscore = true;
        }
    }
    normalized.trim_matches('_').to_string()
}

fn cache_key(ident: &str, row_key: Option<&str>) -> String {
    match row_key {
        Some(row_key) => format!("{ident}@{row_key}"),
        None => ident.to_string(),
    }
}

fn json_path<'a>(value: &'a Value, path: &[&str]) -> Result<&'a Value, String> {
    let mut current = value;
    for part in path {
        current = match current {
            Value::Object(map) => map
                .get(*part)
                .ok_or_else(|| format!("missing JSON field {part:?}"))?,
            Value::Array(items) => {
                let index = part
                    .parse::<usize>()
                    .map_err(|_| format!("invalid JSON array index {part:?}"))?;
                items
                    .get(index)
                    .ok_or_else(|| format!("missing JSON array index {index}"))?
            }
            _ => return Err(format!("missing JSON field {part:?}")),
        };
    }
    Ok(current)
}
