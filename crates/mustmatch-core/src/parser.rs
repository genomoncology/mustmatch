use std::collections::HashMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Block {
    pub language: String,
    pub content: String,
    pub line_start: usize,
    pub name: Option<String>,
    pub context: Vec<String>,
    pub context_lines: Vec<usize>,
    pub directives: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Table {
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
    pub line_start: usize,
    pub context: Vec<String>,
    pub context_lines: Vec<usize>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct ParseResult {
    pub blocks: Vec<Block>,
    pub tables: Vec<Table>,
}

fn parse_info_string(info: &str) -> (String, HashMap<String, String>) {
    if info.trim().is_empty() {
        return (String::new(), HashMap::new());
    }

    let parts = shlex::split(info).unwrap_or_else(|| {
        info.split_whitespace()
            .map(std::string::ToString::to_string)
            .collect()
    });

    if parts.is_empty() {
        return (String::new(), HashMap::new());
    }

    let language = parts[0].to_lowercase();
    let mut directives = HashMap::new();

    for part in parts.into_iter().skip(1) {
        if let Some((key, value)) = part.split_once('=') {
            directives.insert(key.to_string(), value.to_string());
        } else {
            directives.insert(part, String::new());
        }
    }

    (language, directives)
}

fn parse_heading(line: &str) -> Option<(usize, String)> {
    let trimmed = line.trim_start();
    let level = trimmed.chars().take_while(|ch| *ch == '#').count();
    if level == 0 || level > 6 {
        return None;
    }

    let rest = trimmed[level..].trim_start();
    if rest.is_empty() {
        return None;
    }

    let title = rest.trim_end_matches('#').trim_end().trim().to_string();

    if title.is_empty() {
        None
    } else {
        Some((level, title))
    }
}

fn parse_fence_start(line: &str) -> Option<(String, String)> {
    let trimmed = line.trim_start();
    let marker_char = trimmed.chars().next()?;
    if marker_char != '`' && marker_char != '~' {
        return None;
    }

    let marker_len = trimmed.chars().take_while(|ch| *ch == marker_char).count();
    if marker_len < 3 {
        return None;
    }

    let marker = marker_char.to_string().repeat(marker_len);
    let info = trimmed[marker_len..].trim().to_string();
    Some((marker, info))
}

fn parse_table_cells(line: &str) -> Vec<String> {
    let mut trimmed = line.trim();
    if let Some(rest) = trimmed.strip_prefix('|') {
        trimmed = rest;
    }
    if let Some(rest) = trimmed.strip_suffix('|') {
        trimmed = rest;
    }

    trimmed
        .split('|')
        .map(|cell| cell.trim().to_string())
        .collect()
}

fn is_table_separator(line: &str) -> bool {
    let mut trimmed = line.trim();

    if !trimmed.contains('|') || !trimmed.contains('-') {
        return false;
    }

    if let Some(rest) = trimmed.strip_prefix('|') {
        trimmed = rest;
    }
    if let Some(rest) = trimmed.strip_suffix('|') {
        trimmed = rest;
    }

    let cells: Vec<&str> = trimmed.split('|').collect();
    if cells.len() < 2 {
        return false;
    }

    cells.iter().all(|cell| {
        let value = cell.trim();
        !value.is_empty() && value.chars().all(|ch| ch == '-' || ch == ':' || ch == ' ')
    })
}

fn is_table_row(line: &str) -> bool {
    let trimmed = line.trim();
    !trimmed.is_empty() && trimmed.contains('|')
}

pub fn parse_markdown(content: &str) -> ParseResult {
    let lines: Vec<&str> = content.split('\n').collect();
    let mut result = ParseResult::default();
    let mut heading_stack: Vec<(usize, String, usize)> = Vec::new();

    let mut index = 0;
    while index < lines.len() {
        let line = lines[index];

        if let Some((level, title)) = parse_heading(line) {
            while heading_stack
                .last()
                .map(|entry| entry.0 >= level)
                .unwrap_or(false)
            {
                heading_stack.pop();
            }
            heading_stack.push((level, title, index + 1));
            index += 1;
            continue;
        }

        if let Some((marker, info)) = parse_fence_start(line) {
            let (mut language, directives) = parse_info_string(&info);

            let mut code_lines = Vec::new();
            let mut scan = index + 1;
            while scan < lines.len() {
                if lines[scan].trim_start().starts_with(&marker) {
                    break;
                }
                code_lines.push(lines[scan]);
                scan += 1;
            }

            if language == "sh" {
                language = "bash".to_string();
            }

            if language == "bash" || language == "python" {
                let mut content = code_lines.join("\n");
                if !content.is_empty() {
                    content.push('\n');
                }

                result.blocks.push(Block {
                    language,
                    content,
                    line_start: index + 1,
                    name: heading_stack.last().map(|entry| entry.1.clone()),
                    context: heading_stack.iter().map(|entry| entry.1.clone()).collect(),
                    context_lines: heading_stack.iter().map(|entry| entry.2).collect(),
                    directives,
                });
            }

            index = if scan < lines.len() { scan + 1 } else { scan };
            continue;
        }

        if index + 1 < lines.len() && is_table_row(line) && is_table_separator(lines[index + 1]) {
            let headers = parse_table_cells(line);
            if !headers.is_empty() {
                let mut rows = Vec::new();
                let mut scan = index + 2;

                while scan < lines.len() {
                    let row_line = lines[scan];
                    if !is_table_row(row_line) {
                        break;
                    }
                    if parse_fence_start(row_line).is_some() || parse_heading(row_line).is_some() {
                        break;
                    }
                    rows.push(parse_table_cells(row_line));
                    scan += 1;
                }

                result.tables.push(Table {
                    headers,
                    rows,
                    line_start: index + 1,
                    context: heading_stack.iter().map(|entry| entry.1.clone()).collect(),
                    context_lines: heading_stack.iter().map(|entry| entry.2).collect(),
                });

                index = scan;
                continue;
            }
        }

        index += 1;
    }

    result
}

pub fn get_table_for_block(result: &ParseResult, block: &Block) -> Option<Table> {
    let mut preceding_table: Option<Table> = None;

    for table in &result.tables {
        if table.line_start >= block.line_start {
            continue;
        }

        let same_context = table.context == block.context;
        let prefix_context = table.context.len() <= block.context.len()
            && table
                .context
                .iter()
                .zip(block.context.iter())
                .all(|(left, right)| left == right);

        if same_context || prefix_context {
            let replace = preceding_table
                .as_ref()
                .map(|candidate| table.line_start > candidate.line_start)
                .unwrap_or(true);
            if replace {
                preceding_table = Some(table.clone());
            }
        }
    }

    preceding_table
}

#[cfg(test)]
mod tests {
    use super::{get_table_for_block, parse_markdown};

    #[test]
    fn parses_blocks_and_tables_with_context() {
        let source = r#"# Root

## Section A

| input | output |
|-------|--------|
| 2     | 4      |

```python each_row timeout=5
result = {"input": row.input, "output": row.input * 2}
```
"#;

        let parsed = parse_markdown(source);
        assert_eq!(parsed.blocks.len(), 1);
        assert_eq!(parsed.tables.len(), 1);

        let block = &parsed.blocks[0];
        assert_eq!(block.language, "python");
        assert_eq!(
            block.context,
            vec!["Root".to_string(), "Section A".to_string()]
        );
        assert_eq!(
            block.directives.get("each_row").map(String::as_str),
            Some("")
        );
        assert_eq!(
            block.directives.get("timeout").map(String::as_str),
            Some("5")
        );

        let table = get_table_for_block(&parsed, block).expect("table should resolve");
        assert_eq!(
            table.headers,
            vec!["input".to_string(), "output".to_string()]
        );
        assert_eq!(table.rows.len(), 1);
    }

    #[test]
    fn normalizes_sh_to_bash() {
        let source = "```sh\necho hello\n```\n";
        let parsed = parse_markdown(source);
        assert_eq!(parsed.blocks.len(), 1);
        assert_eq!(parsed.blocks[0].language, "bash");
    }
}
