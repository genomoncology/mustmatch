#![allow(unsafe_op_in_unsafe_fn)]

use std::collections::HashMap;

use mustmatch_core::{
    CompareMode, ContainsLineReport, NormalizeOptions, ParseResult, TableRowData,
    analyze_contains_lines as core_analyze_contains_lines,
    build_table_rows as core_build_table_rows, compare as core_compare,
    create_md_fixture as core_create_md_fixture, detect_mode as core_detect_mode,
    get_table_for_block as core_get_table_for_block, normalize as core_normalize,
    parse_markdown as core_parse_markdown, strip_ansi as core_strip_ansi,
};
use pyo3::exceptions::{PyAttributeError, PyIndexError, PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};
use serde_json::Value;

fn json_value_to_py(py: Python<'_>, value: Value) -> PyResult<PyObject> {
    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(v) => Ok(v.into_py(py)),
        Value::Number(v) => {
            if let Some(as_i64) = v.as_i64() {
                Ok(as_i64.into_py(py))
            } else if let Some(as_u64) = v.as_u64() {
                Ok(as_u64.into_py(py))
            } else if let Some(as_f64) = v.as_f64() {
                Ok(as_f64.into_py(py))
            } else {
                Ok(v.to_string().into_py(py))
            }
        }
        Value::String(v) => Ok(v.into_py(py)),
        Value::Array(values) => Ok(values
            .into_iter()
            .map(|item| json_value_to_py(py, item))
            .collect::<PyResult<Vec<PyObject>>>()?
            .into_py(py)),
        Value::Object(values) => {
            let dict = PyDict::new_bound(py);
            for (key, value) in values {
                dict.set_item(key, json_value_to_py(py, value)?)?;
            }
            Ok(dict.into_py(py))
        }
    }
}

fn normalize_lookup(value: &str) -> String {
    let mut normalized = String::with_capacity(value.len());
    let mut prev_underscore = false;

    for ch in value.chars().flat_map(char::to_lowercase) {
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

fn resolve_index(length: usize, index: isize) -> Option<usize> {
    if index >= 0 {
        let idx = index as usize;
        if idx < length { Some(idx) } else { None }
    } else {
        let idx = length as isize + index;
        if idx >= 0 { Some(idx as usize) } else { None }
    }
}

#[pyclass(module = "mustmatch._core", name = "Block")]
#[derive(Clone)]
struct PyBlock {
    inner: mustmatch_core::Block,
}

#[pymethods]
impl PyBlock {
    #[getter]
    fn language(&self) -> String {
        self.inner.language.clone()
    }

    #[getter]
    fn content(&self) -> String {
        self.inner.content.clone()
    }

    #[getter]
    fn line_start(&self) -> usize {
        self.inner.line_start
    }

    #[getter]
    fn name(&self) -> Option<String> {
        self.inner.name.clone()
    }

    #[getter]
    fn context(&self) -> Vec<String> {
        self.inner.context.clone()
    }

    #[getter]
    fn context_lines(&self) -> Vec<usize> {
        self.inner.context_lines.clone()
    }

    #[getter]
    fn directives(&self) -> HashMap<String, String> {
        self.inner.directives.clone()
    }
}

impl PyBlock {
    fn from_inner(inner: mustmatch_core::Block) -> Self {
        Self { inner }
    }
}

#[pyclass(module = "mustmatch._core", name = "Table")]
#[derive(Clone)]
struct PyTable {
    inner: mustmatch_core::Table,
}

#[pymethods]
impl PyTable {
    #[getter]
    fn headers(&self) -> Vec<String> {
        self.inner.headers.clone()
    }

    #[getter]
    fn rows(&self) -> Vec<Vec<String>> {
        self.inner.rows.clone()
    }

    #[getter]
    fn line_start(&self) -> usize {
        self.inner.line_start
    }

    #[getter]
    fn context(&self) -> Vec<String> {
        self.inner.context.clone()
    }

    #[getter]
    fn context_lines(&self) -> Vec<usize> {
        self.inner.context_lines.clone()
    }
}

impl PyTable {
    fn from_inner(inner: mustmatch_core::Table) -> Self {
        Self { inner }
    }
}

#[pyclass(module = "mustmatch._core", name = "ParseResult")]
#[derive(Clone)]
struct PyParseResult {
    inner: ParseResult,
}

#[pymethods]
impl PyParseResult {
    #[getter]
    fn blocks(&self, py: Python<'_>) -> PyResult<Vec<Py<PyBlock>>> {
        self.inner
            .blocks
            .iter()
            .cloned()
            .map(|block| Py::new(py, PyBlock::from_inner(block)))
            .collect()
    }

    #[getter]
    fn tables(&self, py: Python<'_>) -> PyResult<Vec<Py<PyTable>>> {
        self.inner
            .tables
            .iter()
            .cloned()
            .map(|table| Py::new(py, PyTable::from_inner(table)))
            .collect()
    }
}

#[pyclass(module = "mustmatch._core", name = "CompareResult")]
#[derive(Clone)]
struct PyCompareResult {
    #[pyo3(get)]
    matches: bool,
    #[pyo3(get)]
    message: String,
    #[pyo3(get)]
    mode: String,
}

#[pyclass(module = "mustmatch._core", name = "ContainsLineReport")]
#[derive(Clone)]
struct PyContainsLineReport {
    #[pyo3(get)]
    expected_count: usize,
    #[pyo3(get)]
    found_lines: Vec<String>,
    #[pyo3(get)]
    missing_lines: Vec<String>,
    #[pyo3(get)]
    found_message: String,
    #[pyo3(get)]
    missing_message: String,
}

impl PyContainsLineReport {
    fn from_inner(inner: ContainsLineReport) -> Self {
        Self {
            expected_count: inner.expected_count,
            found_message: inner.found_message(),
            missing_message: inner.missing_message(),
            found_lines: inner.found_lines,
            missing_lines: inner.missing_lines,
        }
    }
}

#[pyclass(module = "mustmatch._core", name = "TableRow")]
#[derive(Clone)]
struct PyTableRow {
    inner: TableRowData,
}

#[pymethods]
impl PyTableRow {
    #[getter]
    fn _data(&self) -> Vec<(String, String)> {
        self.inner.entries.clone()
    }

    #[getter]
    fn _coerce(&self) -> Vec<String> {
        self.inner.coerce_columns.iter().cloned().collect()
    }

    fn __getattr__(&self, name: &str, py: Python<'_>) -> PyResult<PyObject> {
        if name.starts_with('_') {
            return Err(PyAttributeError::new_err(name.to_string()));
        }

        match self.inner.get(name) {
            Some(value) => Ok(json_value_to_py(py, value)?),
            None => Err(PyAttributeError::new_err(format!("No column {name:?}"))),
        }
    }

    fn __getitem__(&self, key: &str, py: Python<'_>) -> PyResult<PyObject> {
        match self.inner.get(key) {
            Some(value) => Ok(json_value_to_py(py, value)?),
            None => Err(PyKeyError::new_err(key.to_string())),
        }
    }

    fn keys(&self) -> Vec<String> {
        self.inner.keys()
    }

    fn values(&self, py: Python<'_>) -> PyResult<Vec<PyObject>> {
        self.inner
            .values()
            .into_iter()
            .map(|value| json_value_to_py(py, value))
            .collect()
    }

    fn items(&self, py: Python<'_>) -> PyResult<Vec<(String, PyObject)>> {
        self.inner
            .items()
            .into_iter()
            .map(|(key, value)| Ok((key, json_value_to_py(py, value)?)))
            .collect()
    }
}

impl PyTableRow {
    fn from_inner(inner: TableRowData) -> Self {
        Self { inner }
    }
}

#[pyclass(module = "mustmatch._core", name = "Section")]
#[derive(Clone)]
struct PySection {
    #[pyo3(get)]
    title: String,
    #[pyo3(get)]
    level: usize,
    #[pyo3(get)]
    line: usize,
    #[pyo3(get)]
    parent: Option<String>,
    #[pyo3(get)]
    children: Vec<String>,
}

#[pyclass(module = "mustmatch._core", name = "FixtureTable")]
#[derive(Clone)]
struct PyFixtureTable {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    headers: Vec<String>,
    #[pyo3(get)]
    rows: Vec<Py<PyTableRow>>,
    #[pyo3(get)]
    line: usize,
    #[pyo3(get)]
    section: Option<Py<PySection>>,
}

#[pymethods]
impl PyFixtureTable {
    fn __len__(&self) -> usize {
        self.rows.len()
    }

    fn __getitem__(&self, index: isize) -> PyResult<Py<PyTableRow>> {
        match resolve_index(self.rows.len(), index) {
            Some(idx) => Ok(self.rows[idx].clone()),
            None => Err(PyIndexError::new_err("table row index out of range")),
        }
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<PyObject> {
        let list = PyList::new_bound(py, &self.rows);
        Ok(list.call_method0("__iter__")?.into_py(py))
    }

    fn as_dicts(&self, py: Python<'_>) -> PyResult<Vec<HashMap<String, PyObject>>> {
        self.rows
            .iter()
            .map(|row| {
                let borrowed = row.borrow(py);
                borrowed
                    .inner
                    .items()
                    .into_iter()
                    .map(|(key, value)| Ok((key, json_value_to_py(py, value)?)))
                    .collect()
            })
            .collect()
    }
}

#[pyclass(module = "mustmatch._core", name = "Tables")]
#[derive(Clone)]
struct PyTables {
    tables: Vec<Py<PyFixtureTable>>,
    by_name: HashMap<String, usize>,
}

#[pymethods]
impl PyTables {
    fn __len__(&self) -> usize {
        self.tables.len()
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<PyObject> {
        let list = PyList::new_bound(py, &self.tables);
        Ok(list.call_method0("__iter__")?.into_py(py))
    }

    fn __getattr__(&self, name: &str, py: Python<'_>) -> PyResult<PyObject> {
        if name.starts_with('_') {
            return Err(PyAttributeError::new_err(name.to_string()));
        }

        let key = normalize_lookup(name);
        match self.by_name.get(&key) {
            Some(index) => Ok(self.tables[*index].clone().into_py(py)),
            None => Err(PyAttributeError::new_err(format!("No table {name:?}"))),
        }
    }

    fn __getitem__(&self, key: &Bound<'_, PyAny>, py: Python<'_>) -> PyResult<PyObject> {
        if let Ok(index) = key.extract::<isize>() {
            return match resolve_index(self.tables.len(), index) {
                Some(idx) => Ok(self.tables[idx].clone().into_py(py)),
                None => Err(PyIndexError::new_err("table index out of range")),
            };
        }

        if let Ok(name) = key.extract::<String>() {
            let lookup = normalize_lookup(&name);
            return match self.by_name.get(&lookup) {
                Some(idx) => Ok(self.tables[*idx].clone().into_py(py)),
                None => Err(PyKeyError::new_err(name)),
            };
        }

        Err(PyTypeError::new_err("table key must be int or str"))
    }
}

#[pyclass(module = "mustmatch._core", name = "Sections")]
#[derive(Clone)]
struct PySections {
    sections: Vec<Py<PySection>>,
    by_name: HashMap<String, usize>,
}

#[pymethods]
impl PySections {
    fn __len__(&self) -> usize {
        self.sections.len()
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<PyObject> {
        let list = PyList::new_bound(py, &self.sections);
        Ok(list.call_method0("__iter__")?.into_py(py))
    }

    fn __getattr__(&self, name: &str, py: Python<'_>) -> PyResult<PyObject> {
        if name.starts_with('_') {
            return Err(PyAttributeError::new_err(name.to_string()));
        }

        let key = normalize_lookup(name);
        match self.by_name.get(&key) {
            Some(index) => Ok(self.sections[*index].clone().into_py(py)),
            None => Err(PyAttributeError::new_err(format!("No section {name:?}"))),
        }
    }

    fn __getitem__(&self, key: &Bound<'_, PyAny>, py: Python<'_>) -> PyResult<PyObject> {
        if let Ok(index) = key.extract::<isize>() {
            return match resolve_index(self.sections.len(), index) {
                Some(idx) => Ok(self.sections[idx].clone().into_py(py)),
                None => Err(PyIndexError::new_err("section index out of range")),
            };
        }

        if let Ok(name) = key.extract::<String>() {
            let lookup = normalize_lookup(&name);
            return match self.by_name.get(&lookup) {
                Some(idx) => Ok(self.sections[*idx].clone().into_py(py)),
                None => Err(PyKeyError::new_err(name)),
            };
        }

        Err(PyTypeError::new_err("section key must be int or str"))
    }
}

#[pyclass(module = "mustmatch._core", name = "MD")]
#[derive(Clone)]
struct PyMD {
    #[pyo3(get)]
    tables: Py<PyTables>,
    #[pyo3(get)]
    sections: Py<PySections>,
    #[pyo3(get)]
    current_section: Option<Py<PySection>>,
}

#[pyfunction]
fn parse_markdown(content: &str) -> PyParseResult {
    PyParseResult {
        inner: core_parse_markdown(content),
    }
}

#[pyfunction]
fn get_table_for_block(result: &PyParseResult, block: &PyBlock) -> Option<PyTable> {
    core_get_table_for_block(&result.inner, &block.inner).map(PyTable::from_inner)
}

#[pyfunction]
fn build_table_rows(
    py: Python<'_>,
    headers: Vec<String>,
    row_values: Vec<Vec<String>>,
) -> PyResult<(Vec<String>, Vec<Py<PyTableRow>>)> {
    let (normalized_headers, rows) = core_build_table_rows(&headers, &row_values);
    let py_rows = rows
        .into_iter()
        .map(|row| Py::new(py, PyTableRow::from_inner(row)))
        .collect::<PyResult<Vec<_>>>()?;

    Ok((normalized_headers, py_rows))
}

#[pyfunction]
fn create_md_fixture(
    py: Python<'_>,
    parse_result: &PyParseResult,
    current_block: Option<&PyBlock>,
) -> PyResult<PyMD> {
    let fixture =
        core_create_md_fixture(&parse_result.inner, current_block.map(|block| &block.inner));

    let mut py_sections: Vec<Py<PySection>> = Vec::with_capacity(fixture.sections.len());
    for section in &fixture.sections {
        let parent = section
            .parent
            .and_then(|index| fixture.sections.get(index))
            .map(|parent| parent.title.clone());
        let children = section
            .children
            .iter()
            .filter_map(|index| fixture.sections.get(*index))
            .map(|child| child.title.clone())
            .collect();

        py_sections.push(Py::new(
            py,
            PySection {
                title: section.title.clone(),
                level: section.level,
                line: section.line,
                parent,
                children,
            },
        )?);
    }

    let mut section_lookup = HashMap::new();
    for (index, section) in fixture.sections.iter().enumerate() {
        section_lookup.insert(normalize_lookup(&section.title), index);
    }

    let mut py_tables: Vec<Py<PyFixtureTable>> = Vec::with_capacity(fixture.tables.len());
    let mut table_lookup = HashMap::new();

    for (index, table) in fixture.tables.iter().enumerate() {
        let rows = table
            .rows
            .iter()
            .cloned()
            .map(|row| Py::new(py, PyTableRow::from_inner(row)))
            .collect::<PyResult<Vec<_>>>()?;

        let section = table
            .section_index
            .and_then(|section_index| py_sections.get(section_index).cloned());

        py_tables.push(Py::new(
            py,
            PyFixtureTable {
                name: table.name.clone(),
                headers: table.headers.clone(),
                rows,
                line: table.line,
                section,
            },
        )?);

        table_lookup.insert(normalize_lookup(&table.name), index);
    }

    let tables = Py::new(
        py,
        PyTables {
            tables: py_tables,
            by_name: table_lookup,
        },
    )?;

    let sections = Py::new(
        py,
        PySections {
            sections: py_sections.clone(),
            by_name: section_lookup,
        },
    )?;

    let current_section = fixture
        .current_section
        .and_then(|index| py_sections.get(index).cloned());

    Ok(PyMD {
        tables,
        sections,
        current_section,
    })
}

#[pyfunction(signature = (actual, expected, mode = "exact", subset = false, ignore_case = false))]
fn compare(
    actual: &str,
    expected: &str,
    mode: &str,
    subset: bool,
    ignore_case: bool,
) -> PyCompareResult {
    let mode = mode.parse::<CompareMode>().unwrap_or(CompareMode::Exact);
    let result = core_compare(actual, expected, mode, subset, ignore_case);

    PyCompareResult {
        matches: result.matches,
        message: result.message,
        mode: result.mode.as_str().to_string(),
    }
}

#[pyfunction(signature = (actual, expected, ignore_case = false))]
fn analyze_contains_lines(actual: &str, expected: &str, ignore_case: bool) -> PyContainsLineReport {
    PyContainsLineReport::from_inner(core_analyze_contains_lines(actual, expected, ignore_case))
}

#[pyfunction]
fn detect_mode(expected: &str) -> String {
    core_detect_mode(expected).as_str().to_string()
}

#[pyfunction(signature = (text, strip_ansi = true, normalize_newlines = true, trim = true))]
fn normalize(text: &str, strip_ansi: bool, normalize_newlines: bool, trim: bool) -> String {
    core_normalize(
        text,
        NormalizeOptions {
            strip_ansi,
            normalize_newlines,
            trim,
        },
    )
}

#[pyfunction]
fn strip_ansi(text: &str) -> String {
    core_strip_ansi(text)
}

#[pymodule]
fn _core(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyBlock>()?;
    module.add_class::<PyTable>()?;
    module.add_class::<PyParseResult>()?;
    module.add_class::<PyCompareResult>()?;
    module.add_class::<PyContainsLineReport>()?;
    module.add_class::<PyTableRow>()?;
    module.add_class::<PySection>()?;
    module.add_class::<PyFixtureTable>()?;
    module.add_class::<PyTables>()?;
    module.add_class::<PySections>()?;
    module.add_class::<PyMD>()?;

    module.add_function(wrap_pyfunction!(parse_markdown, module)?)?;
    module.add_function(wrap_pyfunction!(get_table_for_block, module)?)?;
    module.add_function(wrap_pyfunction!(build_table_rows, module)?)?;
    module.add_function(wrap_pyfunction!(create_md_fixture, module)?)?;
    module.add_function(wrap_pyfunction!(compare, module)?)?;
    module.add_function(wrap_pyfunction!(analyze_contains_lines, module)?)?;
    module.add_function(wrap_pyfunction!(detect_mode, module)?)?;
    module.add_function(wrap_pyfunction!(normalize, module)?)?;
    module.add_function(wrap_pyfunction!(strip_ansi, module)?)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::normalize_lookup;

    #[test]
    fn normalize_lookup_strips_punctuation() {
        assert_eq!(
            normalize_lookup("Context-Based Disambiguation: Disease Context"),
            "context_based_disambiguation_disease_context"
        );
    }

    #[test]
    fn normalize_lookup_collapses_separators() {
        assert_eq!(normalize_lookup("  A--B__C  "), "a_b_c");
    }
}
