pub mod coercion;
pub mod comparator;
pub mod fixture;
pub mod normalizer;
pub mod parser;

pub use comparator::{
    CompareMode, CompareResult, compare, contains, detect_mode, exact, extract_regex_pattern,
    json_match, jsonl_match, regex_match,
};
pub use fixture::{
    FixtureTable, MdFixture, SectionData, TableRowData, build_table_rows, create_md_fixture,
};
pub use normalizer::{NormalizeOptions, normalize, normalize_text, strip_ansi};
pub use parser::{Block, ParseResult, Table, get_table_for_block, parse_markdown};

#[cfg(test)]
mod tests {
    use crate::{CompareMode, compare, detect_mode, normalize_text, parse_markdown};

    #[test]
    fn parser_and_compare_smoke() {
        let markdown = r#"# Title

```bash
echo hello
```
"#;

        let parsed = parse_markdown(markdown);
        assert_eq!(parsed.blocks.len(), 1);
        assert_eq!(parsed.blocks[0].line_start, 3);

        let mode = detect_mode("hello");
        let result = compare("hello", "hello", mode, false, false);
        assert!(result.matches);
    }

    #[test]
    fn normalize_then_contains() {
        let actual = normalize_text("  \u{1b}[31mHello World\u{1b}[0m  ");
        let result = compare(&actual, "world", CompareMode::Contains, false, true);
        assert!(result.matches);
    }
}
