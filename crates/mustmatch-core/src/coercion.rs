use regex::Regex;
use serde_json::{Number, Value};
use std::sync::LazyLock;

static INT_RE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^-?\d+$").expect("valid int regex"));
static FLOAT_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^-?\d+\.\d+$").expect("valid float regex"));

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

#[cfg(test)]
mod tests {
    use super::{coerce_value, normalize_key};
    use serde_json::{Number, Value};

    #[test]
    fn coerces_empty_string_to_null() {
        assert_eq!(coerce_value(""), Value::Null);
    }

    #[test]
    fn coerces_whitespace_only_to_null() {
        assert_eq!(coerce_value("  "), Value::Null);
    }

    #[test]
    fn coerces_python_none_to_null() {
        assert_eq!(coerce_value("None"), Value::Null);
    }

    #[test]
    fn coerces_true_lowercase() {
        assert_eq!(coerce_value("true"), Value::Bool(true));
    }

    #[test]
    fn coerces_true_uppercase() {
        assert_eq!(coerce_value("TRUE"), Value::Bool(true));
    }

    #[test]
    fn coerces_false_mixed_case() {
        assert_eq!(coerce_value("False"), Value::Bool(false));
    }

    #[test]
    fn coerces_integer() {
        assert_eq!(coerce_value("42"), Value::Number(Number::from(42)));
    }

    #[test]
    fn coerces_negative_integer() {
        assert_eq!(coerce_value("-7"), Value::Number(Number::from(-7)));
    }

    #[test]
    fn coerces_float() {
        assert_eq!(
            coerce_value("3.14"),
            Value::Number(Number::from_f64(3.14).expect("valid float")),
        );
    }

    #[test]
    fn coerces_negative_float() {
        assert_eq!(
            coerce_value("-0.5"),
            Value::Number(Number::from_f64(-0.5).expect("valid float")),
        );
    }

    #[test]
    fn leaves_plain_string_as_string() {
        assert_eq!(coerce_value("hello"), Value::String("hello".to_string()));
    }

    #[test]
    fn trims_before_coercion() {
        assert_eq!(coerce_value(" 42 "), Value::Number(Number::from(42)));
    }

    #[test]
    fn keeps_i64_overflow_as_string() {
        let overflow = "99999999999999999999";
        assert_eq!(coerce_value(overflow), Value::String(overflow.to_string()));
    }

    #[test]
    fn normalizes_space_in_key() {
        assert_eq!(normalize_key("Some Key"), "some_key");
    }

    #[test]
    fn normalizes_dash_in_key() {
        assert_eq!(normalize_key("my-field"), "my_field");
    }

    #[test]
    fn normalizes_uppercase_key() {
        assert_eq!(normalize_key("UPPER"), "upper");
    }
}
