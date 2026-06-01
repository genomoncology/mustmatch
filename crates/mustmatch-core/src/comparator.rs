use std::collections::BTreeSet;

use regex::RegexBuilder;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use similar::TextDiff;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum CompareMode {
    Exact,
    Contains,
    Regex,
    Json,
    Jsonl,
}

impl CompareMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            CompareMode::Exact => "exact",
            CompareMode::Contains => "contains",
            CompareMode::Regex => "regex",
            CompareMode::Json => "json",
            CompareMode::Jsonl => "jsonl",
        }
    }
}

impl std::str::FromStr for CompareMode {
    type Err = ();

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        Ok(match value {
            "contains" => CompareMode::Contains,
            "regex" => CompareMode::Regex,
            "json" => CompareMode::Json,
            "jsonl" => CompareMode::Jsonl,
            "exact" => CompareMode::Exact,
            _ => return Err(()),
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CompareResult {
    pub matches: bool,
    pub message: String,
    pub mode: CompareMode,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContainsLineReport {
    pub expected_count: usize,
    pub found_lines: Vec<String>,
    pub missing_lines: Vec<String>,
}

impl ContainsLineReport {
    pub fn missing_message(&self) -> String {
        format_missing_lines_message(self)
    }

    pub fn found_message(&self) -> String {
        format_found_lines_message(self)
    }
}

fn parse_regex_literal(value: &str) -> Option<(String, String)> {
    let trimmed = value.trim();
    if !trimmed.starts_with('/') {
        return None;
    }

    let tail = &trimmed[1..];
    let slash_index = tail.rfind('/')?;
    if slash_index == 0 {
        return None;
    }

    let pattern = &tail[..slash_index];
    if pattern.is_empty() {
        return None;
    }

    let flags = &tail[slash_index + 1..];
    if !flags.chars().all(|ch| ch.is_ascii_alphabetic()) {
        return None;
    }

    Some((pattern.to_string(), flags.to_string()))
}

fn generate_diff(actual: &str, expected: &str) -> String {
    TextDiff::from_lines(expected, actual)
        .unified_diff()
        .header("expected", "actual")
        .to_string()
}

pub fn exact(actual: &str, expected: &str) -> CompareResult {
    if actual == expected {
        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Exact,
        };
    }

    CompareResult {
        matches: false,
        message: generate_diff(actual, expected),
        mode: CompareMode::Exact,
    }
}

fn format_missing_lines_message(report: &ContainsLineReport) -> String {
    format!(
        "Missing {} of {} expected lines:\n{}",
        report.missing_lines.len(),
        report.expected_count,
        report
            .missing_lines
            .iter()
            .map(|line| format!("  - {line:?}"))
            .collect::<Vec<_>>()
            .join("\n")
    )
}

fn format_found_lines_message(report: &ContainsLineReport) -> String {
    format!(
        "Found {} of {} forbidden lines:\n{}",
        report.found_lines.len(),
        report.expected_count,
        report
            .found_lines
            .iter()
            .map(|line| format!("  - {line:?}"))
            .collect::<Vec<_>>()
            .join("\n")
    )
}

fn compare_multiline_contains(report: &ContainsLineReport) -> CompareResult {
    if report.missing_lines.is_empty() {
        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Contains,
        };
    }

    CompareResult {
        matches: false,
        message: report.missing_message(),
        mode: CompareMode::Contains,
    }
}

pub fn analyze_contains_lines(
    actual: &str,
    expected: &str,
    ignore_case: bool,
) -> ContainsLineReport {
    let actual_folded = ignore_case.then(|| actual.to_lowercase());
    let mut found_lines = Vec::new();
    let mut missing_lines = Vec::new();

    for line in expected.split('\n') {
        if line.trim().is_empty() {
            continue;
        }

        let found = match &actual_folded {
            Some(actual_folded) => {
                let expected_folded = line.to_lowercase();
                actual_folded.contains(&expected_folded)
            }
            None => actual.contains(line),
        };

        if found {
            found_lines.push(line.to_string());
        } else {
            missing_lines.push(line.to_string());
        }
    }

    ContainsLineReport {
        expected_count: found_lines.len() + missing_lines.len(),
        found_lines,
        missing_lines,
    }
}

pub fn contains(actual: &str, expected: &str) -> CompareResult {
    if has_ellipsis(expected) {
        return compare_ellipsis(actual, expected, false);
    }

    if expected.contains('\n') {
        let report = analyze_contains_lines(actual, expected, false);
        return compare_multiline_contains(&report);
    }

    if actual.contains(expected) {
        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Contains,
        };
    }

    CompareResult {
        matches: false,
        message: format!("Expected substring not found: {expected:?}\nActual: {actual:?}"),
        mode: CompareMode::Contains,
    }
}

/// True when the expected block uses ellipsis (`...`): either a standalone
/// `...` line (skip any number of lines) or a line ending in `...` (match the
/// line as a prefix and ignore the rest). Used to keep doc blocks short and to
/// elide volatile or long output while still anchoring on the lines that matter.
pub fn has_ellipsis(expected: &str) -> bool {
    expected.split('\n').any(|line| {
        let trimmed = line.trim();
        !trimmed.is_empty() && (trimmed == "..." || trimmed.ends_with("..."))
    })
}

enum EllipsisToken {
    /// A standalone `...` line: skip any number of actual lines.
    Gap,
    /// A content line that must be found (as a substring of one actual line).
    Line(String),
}

fn tokenize_ellipsis(expected: &str) -> Vec<EllipsisToken> {
    let mut tokens = Vec::new();
    for raw in expected.split('\n') {
        let line = raw.trim_end();
        if line.trim().is_empty() {
            continue;
        }
        if line.trim() == "..." {
            tokens.push(EllipsisToken::Gap);
            continue;
        }
        // A trailing `...` makes the line a prefix anchor: keep the text before
        // it and ignore the rest of the actual line (it is matched as a
        // substring, so the tail is naturally ignored).
        let text = match line.strip_suffix("...") {
            Some(stripped) => stripped.trim_end().to_string(),
            None => line.to_string(),
        };
        tokens.push(EllipsisToken::Line(text));
    }
    tokens
}

/// Ordered match with explicit `...` gaps. Content lines between gaps must match
/// consecutive actual lines (adjacency is what makes `...` meaningful); a `...`
/// skips any number of lines until the next content anchor is found. The first
/// anchor may appear anywhere (an implicit leading gap) so docs need not anchor
/// on table headers/banners.
pub fn compare_ellipsis(actual: &str, expected: &str, ignore_case: bool) -> CompareResult {
    let tokens = tokenize_ellipsis(expected);
    let actual_lines: Vec<&str> = actual.split('\n').collect();
    // Collapse internal whitespace so a clean doc line (`name | BRAF`) matches
    // padded table output (`name        | BRAF`). Column padding is a rendering
    // artifact, not behaviour, so ellipsis matching is whitespace-insensitive.
    let fold = |value: &str| {
        let collapsed = value.split_whitespace().collect::<Vec<_>>().join(" ");
        if ignore_case {
            collapsed.to_lowercase()
        } else {
            collapsed
        }
    };

    let mut ai = 0usize;
    let mut skip = true; // implicit leading gap: first anchor floats forward
    for token in &tokens {
        match token {
            EllipsisToken::Gap => skip = true,
            EllipsisToken::Line(text) => {
                let needle = fold(text);
                if skip {
                    let mut found = None;
                    while ai < actual_lines.len() {
                        if fold(actual_lines[ai]).contains(&needle) {
                            found = Some(ai);
                            break;
                        }
                        ai += 1;
                    }
                    match found {
                        Some(j) => {
                            ai = j + 1;
                            skip = false;
                        }
                        None => {
                            return CompareResult {
                                matches: false,
                                message: format!(
                                    "Ellipsis match failed: no line containing {text:?} found after the preceding `...`."
                                ),
                                mode: CompareMode::Contains,
                            };
                        }
                    }
                } else if ai < actual_lines.len() && fold(actual_lines[ai]).contains(&needle) {
                    ai += 1;
                } else {
                    let got = actual_lines.get(ai).copied().unwrap_or("<end of output>");
                    return CompareResult {
                        matches: false,
                        message: format!(
                            "Ellipsis match failed: expected the next line to contain {text:?}, got {got:?}. Insert `...` to skip lines."
                        ),
                        mode: CompareMode::Contains,
                    };
                }
            }
        }
    }

    CompareResult {
        matches: true,
        message: String::new(),
        mode: CompareMode::Contains,
    }
}

pub fn regex_match(actual: &str, pattern: &str, case_insensitive: bool) -> CompareResult {
    let mut builder = RegexBuilder::new(pattern);
    builder.case_insensitive(case_insensitive);

    let compiled = match builder.build() {
        Ok(compiled) => compiled,
        Err(err) => {
            let message = err.to_string().replace('\n', " ");
            return CompareResult {
                matches: false,
                message: format!("Invalid regex pattern: {message}"),
                mode: CompareMode::Regex,
            };
        }
    };

    if compiled.is_match(actual) {
        CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Regex,
        }
    } else {
        CompareResult {
            matches: false,
            message: format!("Pattern /{pattern}/ did not match\nActual: {actual:?}"),
            mode: CompareMode::Regex,
        }
    }
}

fn sorted_json(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut sorted = Map::new();
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for key in keys {
                sorted.insert(key.clone(), sorted_json(&map[key]));
            }
            Value::Object(sorted)
        }
        Value::Array(items) => Value::Array(items.iter().map(sorted_json).collect()),
        _ => value.clone(),
    }
}

fn is_subset(subset: &Value, superset: &Value) -> bool {
    match (subset, superset) {
        (Value::Object(left), Value::Object(right)) => left.iter().all(|(key, value)| {
            right
                .get(key)
                .map(|candidate| is_subset(value, candidate))
                .unwrap_or(false)
        }),
        (Value::Array(left), Value::Array(right)) => left
            .iter()
            .all(|value| right.iter().any(|candidate| is_subset(value, candidate))),
        _ => subset == superset,
    }
}

pub fn json_match(actual: &str, expected: &str, subset: bool) -> CompareResult {
    let actual_obj: Value = match serde_json::from_str(actual) {
        Ok(value) => value,
        Err(err) => {
            return CompareResult {
                matches: false,
                message: format!("Invalid JSON in actual: {err}"),
                mode: CompareMode::Json,
            };
        }
    };

    let expected_obj: Value = match serde_json::from_str(expected) {
        Ok(value) => value,
        Err(err) => {
            return CompareResult {
                matches: false,
                message: format!("Invalid JSON in expected: {err}"),
                mode: CompareMode::Json,
            };
        }
    };

    if subset {
        if is_subset(&expected_obj, &actual_obj) {
            return CompareResult {
                matches: true,
                message: String::new(),
                mode: CompareMode::Json,
            };
        }

        return CompareResult {
            matches: false,
            message: format!(
                "Expected subset not found\nExpected: {}\nActual: {}",
                serde_json::to_string_pretty(&expected_obj)
                    .unwrap_or_else(|_| expected.to_string()),
                serde_json::to_string_pretty(&actual_obj).unwrap_or_else(|_| actual.to_string()),
            ),
            mode: CompareMode::Json,
        };
    }

    if actual_obj == expected_obj {
        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Json,
        };
    }

    let actual_formatted = serde_json::to_string_pretty(&sorted_json(&actual_obj))
        .unwrap_or_else(|_| actual.to_string());
    let expected_formatted = serde_json::to_string_pretty(&sorted_json(&expected_obj))
        .unwrap_or_else(|_| expected.to_string());

    CompareResult {
        matches: false,
        message: generate_diff(&actual_formatted, &expected_formatted),
        mode: CompareMode::Json,
    }
}

pub fn jsonl_match(actual: &str, expected: &str, subset: bool) -> CompareResult {
    let actual_lines: Vec<&str> = actual
        .trim()
        .split('\n')
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .collect();

    let expected_lines: Vec<&str> = expected
        .trim()
        .split('\n')
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .collect();

    let mut actual_objects = Vec::with_capacity(actual_lines.len());
    for (index, line) in actual_lines.iter().enumerate() {
        match serde_json::from_str::<Value>(line) {
            Ok(value) => actual_objects.push(value),
            Err(err) => {
                return CompareResult {
                    matches: false,
                    message: format!("Invalid JSON on line {}: {err}", index + 1),
                    mode: CompareMode::Jsonl,
                };
            }
        }
    }

    let mut expected_objects = Vec::with_capacity(expected_lines.len());
    for (index, line) in expected_lines.iter().enumerate() {
        match serde_json::from_str::<Value>(line) {
            Ok(value) => expected_objects.push(value),
            Err(err) => {
                return CompareResult {
                    matches: false,
                    message: format!("Invalid JSON in expected line {}: {err}", index + 1),
                    mode: CompareMode::Jsonl,
                };
            }
        }
    }

    if subset {
        for expected_obj in &expected_objects {
            let found = actual_objects
                .iter()
                .any(|actual_obj| is_subset(expected_obj, actual_obj));
            if !found {
                return CompareResult {
                    matches: false,
                    message: format!(
                        "Expected object not found: {}",
                        serde_json::to_string(expected_obj)
                            .unwrap_or_else(|_| expected_obj.to_string())
                    ),
                    mode: CompareMode::Jsonl,
                };
            }
        }

        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Jsonl,
        };
    }

    if actual_objects == expected_objects {
        return CompareResult {
            matches: true,
            message: String::new(),
            mode: CompareMode::Jsonl,
        };
    }

    CompareResult {
        matches: false,
        message: format!(
            "JSONL mismatch\nExpected {} objects, got {}",
            expected_objects.len(),
            actual_objects.len()
        ),
        mode: CompareMode::Jsonl,
    }
}

pub fn compare(
    actual: &str,
    expected: &str,
    mode: CompareMode,
    subset: bool,
    ignore_case: bool,
) -> CompareResult {
    match mode {
        CompareMode::Exact => {
            if ignore_case && actual.to_lowercase() == expected.to_lowercase() {
                CompareResult {
                    matches: true,
                    message: String::new(),
                    mode: CompareMode::Exact,
                }
            } else {
                exact(actual, expected)
            }
        }
        CompareMode::Contains => {
            if has_ellipsis(expected) {
                return compare_ellipsis(actual, expected, ignore_case);
            }

            if expected.contains('\n') {
                let report = analyze_contains_lines(actual, expected, ignore_case);
                return compare_multiline_contains(&report);
            }

            if ignore_case {
                let actual_folded = actual.to_lowercase();
                let expected_folded = expected.to_lowercase();
                if actual_folded.contains(&expected_folded) {
                    return CompareResult {
                        matches: true,
                        message: String::new(),
                        mode: CompareMode::Contains,
                    };
                }
            }
            contains(actual, expected)
        }
        CompareMode::Regex => {
            let (pattern, flags) = match parse_regex_literal(expected) {
                Some(parsed) => parsed,
                None => {
                    return CompareResult {
                        matches: false,
                        message: "Expected regex literal like /pattern/".to_string(),
                        mode: CompareMode::Regex,
                    };
                }
            };

            let mut unsupported = BTreeSet::new();
            let mut case_insensitive = false;

            for flag in flags.chars() {
                if flag == 'i' {
                    case_insensitive = true;
                } else {
                    unsupported.insert(flag);
                }
            }

            if !unsupported.is_empty() {
                let unsupported_flags: String = unsupported.iter().collect();
                return CompareResult {
                    matches: false,
                    message: format!("Unsupported regex flags: {unsupported_flags}"),
                    mode: CompareMode::Regex,
                };
            }

            regex_match(actual, &pattern, ignore_case || case_insensitive)
        }
        CompareMode::Json => json_match(actual, expected, subset),
        CompareMode::Jsonl => jsonl_match(actual, expected, subset),
    }
}

pub fn detect_mode(expected: &str) -> CompareMode {
    let expected = expected.trim();

    if parse_regex_literal(expected).is_some() {
        return CompareMode::Regex;
    }

    if (expected.starts_with('{') && expected.ends_with('}'))
        || (expected.starts_with('[') && expected.ends_with(']'))
    {
        let lines: Vec<&str> = expected
            .split('\n')
            .map(str::trim)
            .filter(|line| !line.is_empty())
            .collect();

        if lines.len() > 1
            && lines
                .iter()
                .all(|line| line.starts_with('{') && line.ends_with('}'))
        {
            return CompareMode::Jsonl;
        }

        return CompareMode::Json;
    }

    CompareMode::Exact
}

pub fn extract_regex_pattern(expected: &str) -> String {
    parse_regex_literal(expected)
        .map(|(pattern, _)| pattern)
        .unwrap_or_else(|| expected.trim().to_string())
}

#[cfg(test)]
mod tests {
    use super::{
        CompareMode, analyze_contains_lines, compare, contains, detect_mode, has_ellipsis,
        json_match,
    };

    #[test]
    fn detects_modes_like_python() {
        assert_eq!(detect_mode("/foo/"), CompareMode::Regex);
        assert_eq!(detect_mode("{\"a\":1}"), CompareMode::Json);
        assert_eq!(detect_mode("{\"a\":1}\n{\"b\":2}"), CompareMode::Jsonl);
        assert_eq!(detect_mode("hello"), CompareMode::Exact);
    }

    #[test]
    fn json_subset_comparison() {
        let result = json_match("{\"a\":1,\"b\":2}", "{\"a\":1}", true);
        assert!(result.matches);

        let failure = json_match("{\"a\":1}", "{\"a\":2}", true);
        assert!(!failure.matches);
    }

    #[test]
    fn regex_flags_validation() {
        let result = compare("hello", "/HELLO/i", CompareMode::Regex, false, false);
        assert!(result.matches);

        let unsupported = compare("hello", "/hello/g", CompareMode::Regex, false, false);
        assert!(!unsupported.matches);
        assert!(unsupported.message.contains("Unsupported regex flags"));
    }

    #[test]
    fn contains_single_line_behavior_unchanged() {
        let result = contains("alpha beta", "beta");
        assert!(result.matches);

        let failure = contains("alpha beta", "gamma");
        assert!(!failure.matches);
        assert!(
            failure
                .message
                .contains("Expected substring not found: \"gamma\"")
        );
    }

    #[test]
    fn contains_multiline_requires_all_non_empty_lines() {
        let result = contains("alpha beta\ngamma delta", "alpha\ngamma");
        assert!(result.matches);

        let failure = contains("alpha beta\ngamma delta", "alpha\ndelta\nepsilon");
        assert!(!failure.matches);
        assert_eq!(
            failure.message,
            "Missing 1 of 3 expected lines:\n  - \"epsilon\""
        );
    }

    #[test]
    fn contains_multiline_skips_blank_separator_lines() {
        let result = contains("  alpha here\n  beta there", "  alpha\n\n  beta");
        assert!(result.matches);
    }

    #[test]
    fn contains_multiline_preserves_line_whitespace() {
        let result = contains("alpha\n  beta trailer\n gamma", "  beta\n gamma");
        assert!(result.matches);
    }

    #[test]
    fn contains_multiline_ignore_case_uses_per_line_matching() {
        let result = compare(
            "HELLO there\nsome WORLD",
            "hello\nworld",
            CompareMode::Contains,
            false,
            true,
        );
        assert!(result.matches);
    }

    #[test]
    fn contains_multiline_blank_only_expected_is_vacuously_true() {
        let result = contains("anything", "\n  \n");
        assert!(result.matches);
    }

    #[test]
    fn analyze_contains_lines_reports_found_and_missing_lines() {
        let report =
            analyze_contains_lines("alpha\n  beta\nomega", "alpha\n\ngamma\n  beta", false);

        assert_eq!(report.expected_count, 3);
        assert_eq!(
            report.found_lines,
            vec!["alpha".to_string(), "  beta".to_string()]
        );
        assert_eq!(report.missing_lines, vec!["gamma".to_string()]);
    }

    #[test]
    fn format_found_lines_message_lists_forbidden_lines() {
        let report = analyze_contains_lines("alpha\nbeta", "alpha\ngamma", false);

        assert_eq!(
            report.found_message(),
            "Found 1 of 2 forbidden lines:\n  - \"alpha\""
        );
    }

    #[test]
    fn has_ellipsis_detects_standalone_and_trailing() {
        assert!(has_ellipsis("name | BRAF\n...\ndescription | foo"));
        assert!(has_ellipsis("description | Protein kinase that ..."));
        assert!(!has_ellipsis("name | BRAF\ndescription | foo"));
    }

    #[test]
    fn ellipsis_skips_leading_banner_then_matches_adjacent_rows() {
        // psql -x expanded output: a RECORD banner we don't care about, then rows.
        let actual = "-[ RECORD 1 ]----------\n\
                      name | BRAF\n\
                      long_name | B-Raf proto-oncogene, serine/threonine kinase\n\
                      description | Protein kinase that participates in MAPK signalling";
        let expected = "...\n\
                        name | BRAF\n\
                        long_name | B-Raf proto-oncogene, serine/threonine ...\n\
                        description | Protein kinase that ...";
        let result = contains(actual, expected);
        assert!(result.matches, "message: {}", result.message);
    }

    #[test]
    fn ellipsis_gap_skips_any_number_of_lines() {
        let actual = "header\nrow a\nrow b\nrow c\nrow d\nfooter";
        let result = contains(actual, "row a\n...\nfooter");
        assert!(result.matches, "message: {}", result.message);
    }

    #[test]
    fn ellipsis_adjacency_failure_needs_a_gap() {
        // In ellipsis mode (a leading `...` here), content lines with no `...`
        // between them must be adjacent. `row b` sits between, so this fails and
        // the message tells the author to insert `...`.
        let actual = "row a\nrow b\nrow c";
        let failure = contains(actual, "...\nrow a\nrow c");
        assert!(!failure.matches);
        assert!(failure.message.contains("Insert `...` to skip lines"));
    }

    #[test]
    fn plain_multiline_without_ellipsis_stays_unordered() {
        // No `...` anywhere → legacy each-line-appears (order-independent).
        let actual = "row a\nrow b\nrow c";
        assert!(contains(actual, "row c\nrow a").matches);
    }

    #[test]
    fn ellipsis_missing_anchor_after_gap_fails() {
        let actual = "alpha\nbeta\ngamma";
        let failure = contains(actual, "alpha\n...\nomega");
        assert!(!failure.matches);
        assert!(failure.message.contains("omega"));
    }

    #[test]
    fn ellipsis_trailing_prefix_matches_long_value() {
        let actual = "value | the quick brown fox jumps over the lazy dog";
        let result = contains(actual, "value | the quick brown ...");
        assert!(result.matches, "message: {}", result.message);
    }

    #[test]
    fn ellipsis_routes_through_compare_with_ignore_case() {
        let result = compare(
            "HEADER\nNAME | BRAF",
            "...\nname | braf",
            CompareMode::Contains,
            false,
            true,
        );
        assert!(result.matches, "message: {}", result.message);
    }
}
