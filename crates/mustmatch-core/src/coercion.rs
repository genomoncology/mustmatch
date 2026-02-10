use once_cell::sync::Lazy;
use regex::Regex;
use serde_json::{Number, Value};

static INT_RE: Lazy<Regex> = Lazy::new(|| Regex::new(r"^-?\d+$").expect("valid int regex"));
static FLOAT_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^-?\d+\.\d+$").expect("valid float regex"));

pub fn normalize_key(value: &str) -> String {
    value.to_lowercase().replace([' ', '-'], "_")
}

pub fn coerce_value(value: &str) -> Value {
    let stripped = value.trim();

    if stripped.is_empty() || stripped == "None" {
        return Value::Null;
    }

    let lowered = stripped.to_lowercase();
    if lowered == "true" {
        return Value::Bool(true);
    }
    if lowered == "false" {
        return Value::Bool(false);
    }

    if INT_RE.is_match(stripped) {
        if let Ok(v) = stripped.parse::<i64>() {
            return Value::Number(Number::from(v));
        }
    }

    if FLOAT_RE.is_match(stripped) {
        if let Ok(v) = stripped.parse::<f64>() {
            if let Some(number) = Number::from_f64(v) {
                return Value::Number(number);
            }
        }
    }

    Value::String(stripped.to_string())
}
