use std::io::{self, Read};

use mustmatch_core::{
    CompareMode, NormalizeOptions, analyze_contains_lines, compare, detect_mode, normalize,
};

const VERSION: &str = env!("CARGO_PKG_VERSION");
const HELP: &str = "mustmatch-cli - Assert stdin output matches expected value.\n\nUsage:\n    command | mustmatch-cli [not] [like] [-i|--ignore-case] [-q|--quiet] [--] EXPECTED\n\nOptions:\n    -i, --ignore-case    Case-insensitive comparison\n    -q, --quiet          Suppress mismatch output\n    -h, --help           Show this help\n    --version            Show version\n";

#[derive(Debug, Clone)]
struct MatchArgs {
    expected: String,
    negate: bool,
    like: bool,
    ignore_case: bool,
    quiet: bool,
}

fn parse_match_args(args: &[String]) -> Result<MatchArgs, i32> {
    if args.is_empty() {
        eprintln!("Error: expected value required");
        return Err(2);
    }

    let mut ignore_case = false;
    let mut quiet = false;
    let mut positional: Vec<String> = Vec::new();
    let mut expected_separator: Option<usize> = None;

    let mut index = 0;
    while index < args.len() {
        let arg = &args[index];
        if positional.is_empty() && (arg == "-i" || arg == "--ignore-case") {
            ignore_case = true;
        } else if positional.is_empty() && (arg == "-q" || arg == "--quiet") {
            quiet = true;
        } else if arg == "-h" || arg == "--help" {
            println!("{HELP}");
            return Err(0);
        } else if arg == "--version" {
            println!("mustmatch-cli {VERSION}");
            return Err(0);
        } else if arg == "--" {
            expected_separator = Some(positional.len());
            positional.extend_from_slice(&args[index + 1..]);
            break;
        } else if positional.is_empty() && arg.starts_with('-') {
            eprintln!("Error: unknown option: {arg}");
            return Err(2);
        } else {
            positional.push(arg.clone());
        }

        index += 1;
    }

    let mut negate = false;
    let mut like = false;

    let (tokens, expected) = if let Some(separator) = expected_separator {
        let tokens = positional[..separator].to_vec();
        let expected_tokens = positional[separator..].to_vec();
        if expected_tokens.len() != 1 {
            eprintln!("Error: expected value required");
            return Err(2);
        }
        (tokens, expected_tokens[0].clone())
    } else {
        (positional, String::new())
    };

    let mut cursor = 0;
    if cursor < tokens.len() && tokens[cursor] == "not" {
        negate = true;
        cursor += 1;
    }
    if cursor < tokens.len() && tokens[cursor] == "like" {
        like = true;
        cursor += 1;
    }

    let expected = if expected_separator.is_some() {
        if cursor != tokens.len() {
            eprintln!("Error: invalid arguments");
            return Err(2);
        }
        expected
    } else {
        if cursor >= tokens.len() {
            eprintln!("Error: expected value required");
            return Err(2);
        }
        let expected = tokens[cursor].clone();
        cursor += 1;
        if cursor != tokens.len() {
            eprintln!("Error: too many arguments");
            return Err(2);
        }
        expected
    };

    Ok(MatchArgs {
        expected,
        negate,
        like,
        ignore_case,
        quiet,
    })
}

fn is_plain_multiline_like(mode: CompareMode, expected: &str, like: bool) -> bool {
    like && expected.contains('\n') && !matches!(mode, CompareMode::Json | CompareMode::Jsonl)
}

fn evaluate_match(input: &str, args: &MatchArgs) -> (bool, String) {
    let options = NormalizeOptions::default();
    let actual = normalize(input, options);
    let expected = normalize(&args.expected, options);

    let detected_mode = detect_mode(&expected);

    if is_plain_multiline_like(detected_mode, &expected, args.like) {
        let report = analyze_contains_lines(&actual, &expected, args.ignore_case);
        let matches = if args.negate {
            report.found_lines.is_empty()
        } else {
            report.missing_lines.is_empty()
        };

        if matches {
            return (true, String::new());
        }

        let message = if args.negate {
            report.found_message()
        } else {
            report.missing_message()
        };
        return (false, message);
    }

    let mut mode = detected_mode;
    let mut subset = false;

    if args.like {
        if mode == CompareMode::Json {
            subset = true;
            if detect_mode(&actual) == CompareMode::Jsonl {
                mode = CompareMode::Jsonl;
            }
        } else {
            mode = CompareMode::Contains;
        }
    }

    let result = compare(&actual, &expected, mode, subset, args.ignore_case);

    let mut matches = result.matches;
    if args.negate {
        matches = !matches;
    }

    if matches {
        return (true, String::new());
    }

    if args.negate {
        (false, "FAIL: Expected NOT to match, but it did".to_string())
    } else {
        (false, result.message)
    }
}

fn run_match(args: MatchArgs) -> i32 {
    let mut input = String::new();
    if let Err(err) = io::stdin().read_to_string(&mut input) {
        eprintln!("Error: failed to read stdin: {err}");
        return 2;
    }

    let (matches, message) = evaluate_match(&input, &args);
    if matches {
        return 0;
    }

    if !args.quiet {
        eprintln!("{message}");
    }

    1
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();

    if args.len() == 1 {
        if args[0] == "-h" || args[0] == "--help" {
            println!("{HELP}");
            std::process::exit(0);
        }
        if args[0] == "--version" {
            println!("mustmatch-cli {VERSION}");
            std::process::exit(0);
        }
    }

    match parse_match_args(&args) {
        Ok(parsed) => std::process::exit(run_match(parsed)),
        Err(exit_code) => std::process::exit(exit_code),
    }
}

#[cfg(test)]
mod tests {
    use super::{MatchArgs, evaluate_match, parse_match_args};

    #[test]
    fn parses_not_like_sequence() {
        let args = vec!["not".to_string(), "like".to_string(), "error".to_string()];

        let parsed = parse_match_args(&args).expect("valid args");
        assert!(parsed.negate);
        assert!(parsed.like);
        assert_eq!(parsed.expected, "error");
    }

    #[test]
    fn rejects_unknown_option() {
        let args = vec!["--wat".to_string(), "hello".to_string()];
        let result = parse_match_args(&args);
        assert!(matches!(result, Err(2)));
    }

    #[test]
    fn multiline_like_requires_all_lines_and_reports_missing() {
        let args = MatchArgs {
            expected: "PARK2\nNOTCH1".to_string(),
            negate: false,
            like: true,
            ignore_case: false,
            quiet: false,
        };

        let (matches, message) = evaluate_match("PARK2 | causes | omim\n", &args);

        assert!(!matches);
        assert_eq!(message, "Missing 1 of 2 expected lines:\n  - \"NOTCH1\"");
    }

    #[test]
    fn multiline_not_like_fails_when_any_line_is_found() {
        let args = MatchArgs {
            expected: "PARK2\nNOTCH1".to_string(),
            negate: true,
            like: true,
            ignore_case: false,
            quiet: false,
        };

        let (matches, message) = evaluate_match("PARK2 | causes | omim\n", &args);

        assert!(!matches);
        assert_eq!(message, "Found 1 of 2 forbidden lines:\n  - \"PARK2\"");
    }

    #[test]
    fn multiline_like_ignore_case_matches_per_line() {
        let args = MatchArgs {
            expected: "hello\nworld".to_string(),
            negate: false,
            like: true,
            ignore_case: true,
            quiet: false,
        };

        let (matches, message) = evaluate_match("HELLO there\nsome WORLD\n", &args);

        assert!(matches);
        assert!(message.is_empty());
    }
}
