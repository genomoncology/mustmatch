use once_cell::sync::Lazy;
use regex::Regex;
use serde::{Deserialize, Serialize};

static ANSI_ESCAPE_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07").expect("valid ansi regex")
});

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct NormalizeOptions {
    pub strip_ansi: bool,
    pub normalize_newlines: bool,
    pub trim: bool,
}

impl Default for NormalizeOptions {
    fn default() -> Self {
        Self {
            strip_ansi: true,
            normalize_newlines: true,
            trim: true,
        }
    }
}

pub fn strip_ansi(text: &str) -> String {
    ANSI_ESCAPE_PATTERN.replace_all(text, "").to_string()
}

pub fn normalize(text: &str, options: NormalizeOptions) -> String {
    let mut value = text.to_string();

    if options.normalize_newlines {
        value = value.replace("\r\n", "\n").replace('\r', "\n");
    }

    if options.strip_ansi {
        value = strip_ansi(&value);
    }

    if options.trim {
        value = value.trim().to_string();
    }

    value
}

pub fn normalize_text(text: &str) -> String {
    normalize(text, NormalizeOptions::default())
}

#[cfg(test)]
mod tests {
    use super::{NormalizeOptions, normalize, strip_ansi};

    #[test]
    fn strips_ansi_sequences() {
        assert_eq!(strip_ansi("\u{1b}[31mhello\u{1b}[0m"), "hello");
    }

    #[test]
    fn normalizes_newlines_and_trim() {
        let options = NormalizeOptions::default();
        assert_eq!(normalize("  hello\r\n", options), "hello");
    }
}
