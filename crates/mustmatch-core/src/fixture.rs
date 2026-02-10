use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::coercion::{coerce_value, normalize_key};
use crate::parser::{Block, ParseResult};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SectionData {
    pub title: String,
    pub level: usize,
    pub line: usize,
    pub parent: Option<usize>,
    pub children: Vec<usize>,
    pub path: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TableRowData {
    pub entries: Vec<(String, String)>,
    pub coerce_columns: HashSet<String>,
}

impl TableRowData {
    pub fn resolve(&self, name: &str) -> Option<(String, String)> {
        for (key, value) in &self.entries {
            if key == name {
                return Some((key.clone(), value.clone()));
            }
        }

        let normalized = normalize_key(name);
        for (key, value) in &self.entries {
            if normalize_key(key) == normalized {
                return Some((key.clone(), value.clone()));
            }
        }

        None
    }

    pub fn value_for(&self, key: &str, raw: &str) -> Value {
        if self.coerce_columns.contains(key) {
            coerce_value(raw)
        } else {
            Value::String(raw.to_string())
        }
    }

    pub fn get(&self, name: &str) -> Option<Value> {
        let (key, raw) = self.resolve(name)?;
        Some(self.value_for(&key, &raw))
    }

    pub fn keys(&self) -> Vec<String> {
        self.entries.iter().map(|(key, _)| key.clone()).collect()
    }

    pub fn values(&self) -> Vec<Value> {
        self.entries
            .iter()
            .map(|(key, raw)| self.value_for(key, raw))
            .collect()
    }

    pub fn items(&self) -> Vec<(String, Value)> {
        self.entries
            .iter()
            .map(|(key, raw)| (key.clone(), self.value_for(key, raw)))
            .collect()
    }

    pub fn data_map(&self) -> HashMap<String, String> {
        self.entries
            .iter()
            .map(|(key, value)| (key.clone(), value.clone()))
            .collect()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FixtureTable {
    pub name: String,
    pub headers: Vec<String>,
    pub rows: Vec<TableRowData>,
    pub line: usize,
    pub section_index: Option<usize>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct MdFixture {
    pub tables: Vec<FixtureTable>,
    pub sections: Vec<SectionData>,
    pub current_section: Option<usize>,
}

fn prepare_headers(headers: &[String]) -> (Vec<String>, HashSet<String>) {
    let mut cleaned = Vec::with_capacity(headers.len());
    let mut coerce_columns = HashSet::new();

    for raw_header in headers {
        let header = raw_header.trim();
        let lower = header.to_lowercase();

        if lower.starts_with("str:") {
            cleaned.push(header[4..].trim().to_string());
        } else {
            cleaned.push(header.to_string());
            coerce_columns.insert(header.to_string());
        }
    }

    (cleaned, coerce_columns)
}

pub fn build_table_rows(
    headers: &[String],
    row_values: &[Vec<String>],
) -> (Vec<String>, Vec<TableRowData>) {
    let (normalized_headers, coerce_columns) = prepare_headers(headers);

    let rows = row_values
        .iter()
        .map(|row| {
            let entries = normalized_headers
                .iter()
                .zip(row.iter())
                .map(|(header, value)| (header.clone(), value.clone()))
                .collect();

            TableRowData {
                entries,
                coerce_columns: coerce_columns.clone(),
            }
        })
        .collect();

    (normalized_headers, rows)
}

fn path_key(path: &[String]) -> String {
    path.join("\u{001f}")
}

fn get_or_create_section(
    sections_by_path: &mut HashMap<String, usize>,
    all_sections: &mut Vec<SectionData>,
    level: usize,
    title: String,
    path: Vec<String>,
    line: usize,
) -> usize {
    let key = path_key(&path);
    if let Some(index) = sections_by_path.get(&key) {
        return *index;
    }

    let parent = if path.len() > 1 {
        let parent_key = path_key(&path[..path.len() - 1]);
        sections_by_path.get(&parent_key).copied()
    } else {
        None
    };

    let index = all_sections.len();
    all_sections.push(SectionData {
        title,
        level,
        line,
        parent,
        children: Vec::new(),
        path: path.clone(),
    });

    if let Some(parent_index) = parent {
        all_sections[parent_index].children.push(index);
    }

    sections_by_path.insert(key, index);
    index
}

pub fn create_md_fixture(parse_result: &ParseResult, current_block: Option<&Block>) -> MdFixture {
    let mut sections_by_path: HashMap<String, usize> = HashMap::new();
    let mut all_sections = Vec::new();

    for block in &parse_result.blocks {
        for (index, title) in block.context.iter().enumerate() {
            let path = block.context[..=index].to_vec();
            let line = block.context_lines.get(index).copied().unwrap_or(0);
            let _ = get_or_create_section(
                &mut sections_by_path,
                &mut all_sections,
                index + 1,
                title.clone(),
                path,
                line,
            );
        }
    }

    for table in &parse_result.tables {
        for (index, title) in table.context.iter().enumerate() {
            let path = table.context[..=index].to_vec();
            let line = table.context_lines.get(index).copied().unwrap_or(0);
            let _ = get_or_create_section(
                &mut sections_by_path,
                &mut all_sections,
                index + 1,
                title.clone(),
                path,
                line,
            );
        }
    }

    let tables = parse_result
        .tables
        .iter()
        .map(|table| {
            let name = table
                .context
                .last()
                .cloned()
                .unwrap_or_else(|| "unnamed".to_string());
            let section_index = if table.context.is_empty() {
                None
            } else {
                sections_by_path.get(&path_key(&table.context)).copied()
            };

            let (headers, rows) = build_table_rows(&table.headers, &table.rows);

            FixtureTable {
                name,
                headers,
                rows,
                line: table.line_start,
                section_index,
            }
        })
        .collect();

    let current_section = current_block.and_then(|block| {
        if block.context.is_empty() {
            None
        } else {
            sections_by_path.get(&path_key(&block.context)).copied()
        }
    });

    MdFixture {
        tables,
        sections: all_sections,
        current_section,
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use crate::parser::parse_markdown;

    use super::{build_table_rows, create_md_fixture};

    #[test]
    fn table_rows_apply_coercion_rules() {
        let headers = vec!["value".to_string(), "str:raw".to_string()];
        let rows = vec![vec!["42".to_string(), "42".to_string()]];

        let (_, built_rows) = build_table_rows(&headers, &rows);
        assert_eq!(built_rows.len(), 1);

        let row = &built_rows[0];
        assert_eq!(row.get("value"), Some(json!(42)));
        assert_eq!(row.get("raw"), Some(json!("42")));
    }

    #[test]
    fn builds_md_fixture_sections_and_current_section() {
        let source = r#"# Alpha

## Beta

| input | output |
|-------|--------|
| 2     | 4      |

```python
print("ok")
```
"#;

        let parsed = parse_markdown(source);
        let block = parsed.blocks.first().expect("one block");
        let fixture = create_md_fixture(&parsed, Some(block));

        assert_eq!(fixture.sections.len(), 2);
        assert_eq!(fixture.tables.len(), 1);
        assert!(fixture.current_section.is_some());
    }
}
