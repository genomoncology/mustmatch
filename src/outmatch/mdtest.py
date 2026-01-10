"""Test command: run bash blocks in markdown files."""

from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

# Regex patterns for markdown parsing
FENCE_PATTERN = re.compile(
    r'^```(bash|sh|shell)\s*$\n(.*?)^```\s*$',
    re.MULTILINE | re.DOTALL
)
METADATA_PATTERN = re.compile(
    r'<!--\s*outmatch:\s*(.*?)\s*-->',
    re.IGNORECASE
)
OUTMATCH_PATTERN = re.compile(r'\|\s*outmatch\b')

# Default exclusion patterns
DEFAULT_EXCLUDE_DIRS = frozenset({
    'node_modules', '.git', '_site', 'build', 'dist',
    '__pycache__', '.pytest_cache', '.venv', 'venv',
})


class BlockStatus(Enum):
    """Status of a test block."""
    PENDING = auto()
    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()
    TIMEOUT = auto()


@dataclass
class BlockMetadata:
    """Metadata parsed from markdown comments."""
    skip: bool = False
    skip_if: str | None = None
    timeout: int | None = None
    env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse(cls, text: str) -> BlockMetadata:
        """Parse metadata from directive text."""
        meta = cls()
        for part in text.split():
            if part == 'skip':
                meta.skip = True
            elif part.startswith('skip-if='):
                meta.skip_if = part[8:]
            elif part.startswith('timeout='):
                try:
                    meta.timeout = int(part[8:])
                except ValueError:
                    pass
            elif part.startswith('env='):
                for pair in part[4:].split(','):
                    if '=' in pair:
                        key, val = pair.split('=', 1)
                        meta.env[key] = val
        return meta


@dataclass
class Block:
    """A bash code block from markdown."""
    content: str
    line_start: int
    line_end: int
    name: str | None = None
    metadata: BlockMetadata = field(default_factory=BlockMetadata)


@dataclass
class BlockResult:
    """Result of executing a block."""
    block: Block
    status: BlockStatus
    duration: float = 0.0
    error: str | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass
class FileResult:
    """Result of testing a file."""
    path: Path
    blocks: list[BlockResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for b in self.blocks if b.status == BlockStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for b in self.blocks if b.status == BlockStatus.FAILED)

    @property
    def skipped(self) -> int:
        return sum(1 for b in self.blocks if b.status == BlockStatus.SKIPPED)

    @property
    def timeout(self) -> int:
        return sum(1 for b in self.blocks if b.status == BlockStatus.TIMEOUT)


@dataclass
class RunResult:
    """Overall test result."""
    files: list[FileResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def total(self) -> int:
        return sum(len(f.blocks) for f in self.files)

    @property
    def passed(self) -> int:
        return sum(f.passed for f in self.files)

    @property
    def failed(self) -> int:
        return sum(f.failed for f in self.files)

    @property
    def skipped(self) -> int:
        return sum(f.skipped for f in self.files)

    @property
    def timeout(self) -> int:
        return sum(f.timeout for f in self.files)


# Alias for backward compatibility
TestResult = RunResult


@dataclass
class RunConfig:
    """Configuration for test command."""
    quiet: bool = False
    verbose: bool = False
    fail_fast: bool = False
    parallel: int = 4
    timeout: int = 30
    shell: str = "/bin/bash"
    include_pattern: str | None = None
    exclude_pattern: str | None = None
    line_filter: int | None = None
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path | None = None
    junit_xml: Path | None = None
    json_output: Path | None = None
    tap_output: bool = False


# Alias for backward compatibility
TestConfig = RunConfig


def parse_markdown(content: str, heading_context: bool = True) -> list[Block]:
    """Parse markdown content and extract bash blocks."""
    blocks: list[Block] = []
    lines = content.split('\n')

    # Track current heading for block names
    current_heading: str | None = None
    pending_metadata: BlockMetadata | None = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Track headings for block names
        if heading_context and line.startswith('#'):
            match = re.match(r'^#+\s+(.+)$', line)
            if match:
                current_heading = match.group(1).strip()

        # Check for metadata comment
        meta_match = METADATA_PATTERN.search(line)
        if meta_match:
            pending_metadata = BlockMetadata.parse(meta_match.group(1))
            i += 1
            continue

        # Check for bash fence
        fence_match = re.match(r'^```(bash|sh|shell)\s*$', line)
        if fence_match:
            block_start = i + 1  # Line number (1-indexed)
            block_lines: list[str] = []
            i += 1

            # Collect block content until closing fence
            while i < len(lines) and not lines[i].startswith('```'):
                block_lines.append(lines[i])
                i += 1

            block_end = i + 1  # Line number (1-indexed)
            block_content = '\n'.join(block_lines)

            # Extract name from first comment or heading
            block_name = current_heading
            if block_lines:
                first_line = block_lines[0].strip()
                if first_line.startswith('#'):
                    comment_match = re.match(r'^#\s*(.+)$', first_line)
                    if comment_match:
                        block_name = comment_match.group(1).strip()

            block = Block(
                content=block_content,
                line_start=block_start,
                line_end=block_end,
                name=block_name,
                metadata=pending_metadata or BlockMetadata(),
            )
            blocks.append(block)
            pending_metadata = None

        i += 1

    return blocks


def should_skip_block(block: Block, config: TestConfig) -> bool:
    """Check if block should be skipped."""
    # Skip directive
    if block.metadata.skip:
        return True

    # Skip-if directive (check env var)
    if block.metadata.skip_if:
        import os
        if os.environ.get(block.metadata.skip_if):
            return True

    # Line filter
    if config.line_filter is not None:
        if not (block.line_start <= config.line_filter <= block.line_end):
            return True

    # Include pattern
    if config.include_pattern:
        pattern = re.compile(config.include_pattern, re.IGNORECASE)
        if not pattern.search(block.content):
            if block.name and not pattern.search(block.name):
                return True
            elif not block.name:
                return True

    # Exclude pattern
    if config.exclude_pattern:
        pattern = re.compile(config.exclude_pattern, re.IGNORECASE)
        if pattern.search(block.content):
            return True
        if block.name and pattern.search(block.name):
            return True

    return False


def execute_block(
    block: Block,
    config: TestConfig,
    env: dict[str, str] | None = None,
) -> BlockResult:
    """Execute a single bash block."""
    import os
    import time

    start_time = time.time()

    # Build environment
    block_env = os.environ.copy()
    block_env.update(config.env)
    block_env.update(block.metadata.env)
    if env:
        block_env.update(env)

    # Determine timeout
    timeout = block.metadata.timeout or config.timeout

    # Determine working directory
    cwd = config.cwd

    try:
        proc = subprocess.Popen(
            [config.shell, "-c", block.content],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=block_env,
            cwd=cwd,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            duration = time.time() - start_time
            return BlockResult(
                block=block,
                status=BlockStatus.TIMEOUT,
                duration=duration,
                error=f"Block exceeded {timeout}s timeout",
            )

        duration = time.time() - start_time

        # Check exit code
        if proc.returncode != 0:
            return BlockResult(
                block=block,
                status=BlockStatus.FAILED,
                duration=duration,
                error=f"Exit code {proc.returncode}",
                actual=stderr or stdout,
            )

        return BlockResult(
            block=block,
            status=BlockStatus.PASSED,
            duration=duration,
        )

    except OSError as e:
        # Handle file not found, permission errors, etc.
        duration = time.time() - start_time
        return BlockResult(
            block=block,
            status=BlockStatus.FAILED,
            duration=duration,
            error=f"OS error: {e}",
        )
    except subprocess.SubprocessError as e:
        # Handle subprocess-specific errors
        duration = time.time() - start_time
        return BlockResult(
            block=block,
            status=BlockStatus.FAILED,
            duration=duration,
            error=f"Subprocess error: {e}",
        )


def run_file(path: Path, config: TestConfig) -> FileResult:
    """Test all blocks in a markdown file."""
    import time

    start_time = time.time()
    result = FileResult(path=path)

    try:
        content = path.read_text()
    except OSError:
        # Return empty result with error
        result.duration = time.time() - start_time
        return result

    blocks = parse_markdown(content)

    # Set working directory to file's directory if not specified
    file_config = TestConfig(
        quiet=config.quiet,
        verbose=config.verbose,
        fail_fast=config.fail_fast,
        parallel=config.parallel,
        timeout=config.timeout,
        shell=config.shell,
        include_pattern=config.include_pattern,
        exclude_pattern=config.exclude_pattern,
        line_filter=config.line_filter,
        env=config.env.copy(),
        cwd=config.cwd or path.parent,
        junit_xml=config.junit_xml,
        json_output=config.json_output,
        tap_output=config.tap_output,
    )

    # Execute blocks sequentially in isolated subprocesses
    # Note: Each block runs in a fresh shell, so environment changes
    # (like `export FOO=bar`) don't persist between blocks.
    # Put dependent commands in a single block if state sharing is needed.
    for block in blocks:
        if should_skip_block(block, file_config):
            result.blocks.append(BlockResult(
                block=block,
                status=BlockStatus.SKIPPED,
            ))
            continue

        block_result = execute_block(block, file_config)
        result.blocks.append(block_result)

        # Stop on first failure if fail-fast
        if config.fail_fast and block_result.status == BlockStatus.FAILED:
            break

    result.duration = time.time() - start_time
    return result


def discover_files(
    paths: list[Path],
    exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[Path]:
    """Discover markdown files from paths."""
    files: list[Path] = []

    for path in paths:
        if path.is_file():
            if path.suffix == '.md':
                files.append(path)
        elif path.is_dir():
            for md_file in path.rglob('*.md'):
                # Skip excluded directories
                if any(part in exclude_dirs for part in md_file.parts):
                    continue
                files.append(md_file)

    # Sort for deterministic order
    return sorted(files)


def run_tests(paths: list[Path], config: TestConfig) -> TestResult:
    """Run tests on markdown files."""
    import time

    start_time = time.time()
    result = TestResult()

    # Discover files
    files = discover_files(paths)

    if not files:
        result.duration = time.time() - start_time
        return result

    # Run tests in parallel across files (ThreadPool for I/O-bound subprocess work)
    if config.parallel > 1 and len(files) > 1:
        with ThreadPoolExecutor(max_workers=config.parallel) as executor:
            futures = {
                executor.submit(run_file, f, config): f
                for f in files
            }
            for future in as_completed(futures):
                try:
                    file_result = future.result()
                    result.files.append(file_result)
                except Exception:
                    # Handle execution errors
                    path = futures[future]
                    result.files.append(FileResult(path=path))

                # Check fail-fast
                if config.fail_fast and result.failed > 0:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
    else:
        # Sequential execution
        for path in files:
            file_result = run_file(path, config)
            result.files.append(file_result)

            if config.fail_fast and result.failed > 0:
                break

    result.duration = time.time() - start_time
    return result


# Output formatting functions

def format_block_name(block: Block) -> str:
    """Format block name for display."""
    if block.name:
        return f"Block (line {block.line_start}): {block.name}"
    return f"Block (line {block.line_start})"


def format_result_quiet(result: TestResult) -> str:
    """Format result in quiet mode."""
    total = result.total
    passed = result.passed
    failed = result.failed
    skipped = result.skipped

    status = "✓" if failed == 0 else "✗"
    parts = [f"{status} {passed} passed"]
    if failed > 0:
        parts.append(f"✗ {failed} failed")
    if skipped > 0:
        parts.append(f"⊘ {skipped} skipped")
    parts.append(f"{total} total")

    return ", ".join(parts)


def format_result_default(result: TestResult) -> str:
    """Format result in default mode."""
    lines: list[str] = []

    for file_result in result.files:
        lines.append(f"\nRunning tests in {file_result.path}...")
        lines.append("")

        for block_result in file_result.blocks:
            name = format_block_name(block_result.block)
            if block_result.status == BlockStatus.PASSED:
                lines.append(f"  ✓ {name}")
            elif block_result.status == BlockStatus.FAILED:
                lines.append(f"  ✗ {name}")
            elif block_result.status == BlockStatus.SKIPPED:
                lines.append(f"  ⊘ {name} (skipped)")
            elif block_result.status == BlockStatus.TIMEOUT:
                lines.append(f"  ⏱ {name} (timeout)")

    lines.append("")
    passed, failed, total = result.passed, result.failed, result.total
    lines.append(f"Results: {passed} passed, {failed} failed, {total} total")
    return "\n".join(lines)


def format_result_verbose(result: TestResult) -> str:
    """Format result in verbose mode."""
    lines: list[str] = []

    for file_result in result.files:
        lines.append(f"\nRunning tests in {file_result.path}...")
        lines.append("")

        for block_result in file_result.blocks:
            name = format_block_name(block_result.block)
            if block_result.status == BlockStatus.PASSED:
                lines.append(f"  ✓ {name}")
            elif block_result.status == BlockStatus.FAILED:
                lines.append(f"  ✗ {name}")
                lines.append("")
                lines.append("    Command:")
                for line in block_result.block.content.split('\n')[:5]:
                    lines.append(f"      {line}")
                if len(block_result.block.content.split('\n')) > 5:
                    lines.append("      ...")
                lines.append("")
                if block_result.error:
                    lines.append(f"    Error: {block_result.error}")
                if block_result.actual:
                    lines.append("    Output:")
                    for line in block_result.actual.split('\n')[:10]:
                        lines.append(f"      {line}")
                    if len(block_result.actual.split('\n')) > 10:
                        lines.append("      ...")
                lines.append("")
                blk = block_result.block
                lines.append(f"    {file_result.path}:{blk.line_start}-{blk.line_end}")
                lines.append("")
            elif block_result.status == BlockStatus.SKIPPED:
                lines.append(f"  ⊘ {name} (skipped)")
            elif block_result.status == BlockStatus.TIMEOUT:
                lines.append(f"  ⏱ {name} (timeout)")
                lines.append(f"    {block_result.error}")
                lines.append("")

    lines.append("")
    passed, failed, total = result.passed, result.failed, result.total
    lines.append(f"Results: {passed} passed, {failed} failed, {total} total")
    return "\n".join(lines)


def format_result(result: TestResult, config: TestConfig) -> str:
    """Format test result based on config."""
    if config.quiet:
        return format_result_quiet(result)
    elif config.verbose:
        return format_result_verbose(result)
    else:
        return format_result_default(result)


def write_junit_xml(result: TestResult, path: Path) -> None:
    """Write JUnit XML report."""
    testsuite = ET.Element("testsuite")
    testsuite.set("name", "outmatch")
    testsuite.set("tests", str(result.total))
    testsuite.set("failures", str(result.failed))
    testsuite.set("errors", str(result.timeout))
    testsuite.set("time", f"{result.duration:.2f}")

    for file_result in result.files:
        path_str = str(file_result.path).replace("/", ".").replace("\\", ".")
        classname = path_str.rstrip(".md")
        for block_result in file_result.blocks:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("classname", classname)
            testcase.set("name", format_block_name(block_result.block))
            testcase.set("time", f"{block_result.duration:.2f}")

            if block_result.status == BlockStatus.FAILED:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", block_result.error or "Assertion failed")
                if block_result.actual:
                    failure.text = f"Output:\n{block_result.actual}"
            elif block_result.status == BlockStatus.TIMEOUT:
                error = ET.SubElement(testcase, "error")
                error.set("message", block_result.error or "Timeout")
            elif block_result.status == BlockStatus.SKIPPED:
                ET.SubElement(testcase, "skipped")

    tree = ET.ElementTree(testsuite)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=True)


def write_json_report(result: TestResult, path: Path) -> None:
    """Write JSON report."""
    import json

    data = {
        "summary": {
            "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped,
            "duration": result.duration,
        },
        "files": [],
    }

    for file_result in result.files:
        file_data = {
            "path": str(file_result.path),
            "blocks": [],
        }
        for block_result in file_result.blocks:
            block_data = {
                "line": block_result.block.line_start,
                "name": block_result.block.name,
                "status": block_result.status.name.lower(),
                "duration": block_result.duration,
            }
            if block_result.error:
                block_data["error"] = block_result.error
            if block_result.expected:
                block_data["expected"] = block_result.expected
            if block_result.actual:
                block_data["actual"] = block_result.actual
            file_data["blocks"].append(block_data)
        data["files"].append(file_data)

    path.write_text(json.dumps(data, indent=2))


def format_tap(result: TestResult) -> str:
    """Format result as TAP (Test Anything Protocol)."""
    lines = ["TAP version 13", f"1..{result.total}"]

    test_num = 0
    for file_result in result.files:
        for block_result in file_result.blocks:
            test_num += 1
            name = f"{file_result.path}:{block_result.block.line_start}"
            if block_result.block.name:
                name += f" {block_result.block.name}"

            if block_result.status == BlockStatus.PASSED:
                lines.append(f"ok {test_num} - {name}")
            elif block_result.status == BlockStatus.FAILED:
                lines.append(f"not ok {test_num} - {name}")
                lines.append("  ---")
                if block_result.error:
                    lines.append(f"  message: {block_result.error}")
                if block_result.actual:
                    lines.append(f"  actual: {block_result.actual[:200]}")
                lines.append("  ...")
            elif block_result.status == BlockStatus.SKIPPED:
                lines.append(f"ok {test_num} - {name} # SKIP")
            elif block_result.status == BlockStatus.TIMEOUT:
                lines.append(f"not ok {test_num} - {name} # TIMEOUT")

    return "\n".join(lines)


def run_command(
    paths: list[Path],
    config: TestConfig,
) -> int:
    """Main entry point for test command."""
    # Use current directory if no paths specified
    if not paths:
        paths = [Path.cwd()]

    result = run_tests(paths, config)

    # Write reports
    if config.junit_xml:
        write_junit_xml(result, config.junit_xml)

    if config.json_output:
        write_json_report(result, config.json_output)

    # Output to stdout
    if config.tap_output:
        print(format_tap(result))
    else:
        print(format_result(result, config))

    # Exit code
    if result.failed > 0 or result.timeout > 0:
        return 1
    return 0


# Aliases for backward compatibility (avoid pytest collection issues with test_ prefix)
test_command = run_command
test_file = run_file
