use mustmatch_core::{CompareMode, compare};

pub(crate) fn mode(directives: &std::collections::HashMap<String, String>) -> &'static str {
    if directives.contains_key("not-contains") || directives.contains_key("not_contains") {
        "not-contains"
    } else if directives.contains_key("equals") {
        "equals"
    } else {
        "contains"
    }
}

pub(crate) fn assert_output_matches(
    actual: &str,
    expected: &str,
    language: &str,
    mode: &str,
) -> Result<(), String> {
    if mode == "not-contains" {
        let needles: Vec<&str> = expected
            .lines()
            .filter(|line| !line.trim().is_empty())
            .collect();
        for needle in needles {
            if actual.contains(needle) {
                return Err(format!("Output unexpectedly contained:\n{needle}"));
            }
        }
        return Ok(());
    }

    let (compare_mode, subset) = if language == "json" && mode != "equals" {
        (CompareMode::Json, true)
    } else if mode == "equals" {
        (CompareMode::Exact, false)
    } else {
        (CompareMode::Contains, false)
    };

    let result = compare(actual, expected, compare_mode, subset, false);
    if result.matches {
        Ok(())
    } else {
        Err(result.message)
    }
}
