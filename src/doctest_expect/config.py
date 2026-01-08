"""Configuration dataclasses for doctest-expect."""

from dataclasses import dataclass, field
from enum import Enum, auto


class CompareMode(Enum):
    """Comparison mode for expect."""

    EXACT = auto()
    CONTAINS = auto()
    REGEX = auto()
    JSON = auto()
    JSONL = auto()
    JSONL_SET = auto()
    JSONL_KEY = auto()
    JSONL_CONTAINS = auto()


class ColorMode(Enum):
    """Color output mode."""

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


@dataclass(frozen=True)
class NormalizeOptions:
    """Options for text normalization/preprocessing."""

    strip_ansi: bool = False
    normalize_newlines: bool = False
    trim: bool = False
    collapse_whitespace: bool = False
    ignore_case: bool = False
    replacements: tuple[tuple[str, str], ...] = ()
    redactions: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompareResult:
    """Result of a comparison operation."""

    success: bool
    message: str = ""


@dataclass(frozen=True)
class ExpectConfig:
    """Full configuration for an expect operation."""

    mode: CompareMode = CompareMode.EXACT
    normalize: NormalizeOptions = field(default_factory=NormalizeOptions)
    json_ignore_paths: tuple[str, ...] = ()
    jsonl_key_field: str | None = None
    quiet: bool = False
    color: ColorMode = ColorMode.AUTO
    diff_context: int = 3
    update_file: bool = False
