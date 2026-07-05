"""Multi-language AST parser (tree-sitter) that extracts function-level units.

Supports Python, JavaScript, TypeScript, Go, and C++. If tree-sitter grammars
are unavailable it degrades to a lightweight regex parser so the rest of the
pipeline still functions (PRD §7.1).
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Map file extensions to language names.
EXT_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
}

# tree-sitter node types that represent a function/method per language.
FUNCTION_NODE_TYPES: dict[str, set[str]] = {
    "python": {"function_definition"},
    "javascript": {"function_declaration", "method_definition", "arrow_function"},
    "typescript": {"function_declaration", "method_definition", "arrow_function"},
    "go": {"function_declaration", "method_declaration"},
    "cpp": {"function_definition"},
}


@dataclass
class ParsedFunction:
    """A single function extracted from source (PRD §7.1 data structure)."""

    id: str
    file_path: str
    language: str
    function_name: str
    start_line: int
    end_line: int
    source_text: str
    calls: list[str] = field(default_factory=list)
    called_by: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "language": self.language,
            "function_name": self.function_name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_hash": self.content_hash,
        }


def function_id(file_path: str, name: str, start_line: int) -> str:
    return "sha256:" + hashlib.sha256(f"{file_path}:{name}:{start_line}".encode()).hexdigest()[:32]


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def detect_language(file_path: str) -> str | None:
    return EXT_TO_LANG.get(Path(file_path).suffix.lower())


class ASTParser:
    """Parses source files into `ParsedFunction` units.

    Lazily loads tree-sitter grammars; on failure, falls back to regex parsing.
    """

    def __init__(self) -> None:
        self._parsers: dict[str, Any] = {}
        self._tree_sitter_ready = self._try_load_tree_sitter()

    def _try_load_tree_sitter(self) -> bool:
        # Preferred: the bundled tree_sitter_languages (one dep, all grammars).
        try:
            from tree_sitter_languages import get_parser  # type: ignore

            self._get_parser = get_parser  # type: ignore[assignment]
            return True
        except Exception:  # noqa: BLE001 - try per-language grammar modules next
            pass
        # Fallback: individual tree-sitter-<lang> packages (work on Python 3.12+).
        try:
            from tree_sitter import Language, Parser

            loaders = {
                "python": ("tree_sitter_python", "language"),
                "javascript": ("tree_sitter_javascript", "language"),
                "typescript": ("tree_sitter_typescript", "language_typescript"),
                "go": ("tree_sitter_go", "language"),
                "cpp": ("tree_sitter_cpp", "language"),
            }
            import importlib

            for lang, (module_name, fn_name) in loaders.items():
                try:
                    mod = importlib.import_module(module_name)
                    self._parsers[lang] = Parser(Language(getattr(mod, fn_name)()))
                except Exception as exc:  # noqa: BLE001 - skip grammars not installed
                    logger.debug("grammar %s unavailable: %s", lang, exc)
            if self._parsers:
                self._get_parser = None  # signals per-language dict mode
                return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("tree-sitter core unavailable: %s", exc)
        logger.warning("tree-sitter unavailable, using regex fallback parser")
        return False

    def _parser_for(self, language: str) -> Any:
        """Return a tree-sitter Parser for a language, from either load mode."""
        if getattr(self, "_get_parser", None) is not None:
            return self._get_parser(language)
        return self._parsers.get(language)

    def parse_file(self, file_path: str, source: str | None = None) -> list[ParsedFunction]:
        """Parse a file and return its functions. Reads from disk if source is None."""
        language = detect_language(file_path)
        if language is None:
            return []
        if source is None:
            try:
                source = Path(file_path).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.error("Cannot read %s: %s", file_path, exc)
                return []

        if self._tree_sitter_ready:
            try:
                return self._parse_tree_sitter(file_path, language, source)
            except Exception as exc:  # noqa: BLE001 - never fail the pipeline
                logger.warning("tree-sitter parse failed for %s, falling back: %s", file_path, exc)
        return self._parse_regex(file_path, language, source)

    # ── tree-sitter path ────────────────────────────────
    def _parse_tree_sitter(
        self, file_path: str, language: str, source: str
    ) -> list[ParsedFunction]:
        parser = self._parser_for(language)
        if parser is None:
            return self._parse_regex(file_path, language, source)
        tree = parser.parse(source.encode())
        wanted = FUNCTION_NODE_TYPES.get(language, {"function_definition"})
        functions: list[ParsedFunction] = []
        source_bytes = source.encode()

        def node_name(node: Any) -> str:
            for child in node.children:
                if child.type in ("identifier", "name", "field_identifier"):
                    return source_bytes[child.start_byte : child.end_byte].decode(errors="replace")
            return "<anonymous>"

        def walk(node: Any) -> None:
            if node.type in wanted:
                text = source_bytes[node.start_byte : node.end_byte].decode(errors="replace")
                name = node_name(node)
                start = node.start_point[0] + 1
                functions.append(
                    ParsedFunction(
                        id=function_id(file_path, name, start),
                        file_path=file_path,
                        language=language,
                        function_name=name,
                        start_line=start,
                        end_line=node.end_point[0] + 1,
                        source_text=text,
                        content_hash=content_hash(text),
                        calls=self._extract_calls(text),
                    )
                )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return functions

    # ── regex fallback ──────────────────────────────────
    _REGEX_BY_LANG: dict[str, re.Pattern[str]] = {
        "python": re.compile(r"^\s*def\s+(\w+)\s*\(", re.MULTILINE),
        "javascript": re.compile(r"\bfunction\s+(\w+)\s*\(|(\w+)\s*[:=]\s*(?:async\s*)?\("),
        "typescript": re.compile(r"\bfunction\s+(\w+)\s*\(|(\w+)\s*[:=]\s*(?:async\s*)?\("),
        "go": re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(", re.MULTILINE),
        "cpp": re.compile(r"^\s*[\w:<>*&\s]+?\s+(\w+)\s*\([^;]*\)\s*\{", re.MULTILINE),
    }

    def _parse_regex(self, file_path: str, language: str, source: str) -> list[ParsedFunction]:
        pattern = self._REGEX_BY_LANG.get(language)
        if pattern is None:
            return []
        lines = source.splitlines()
        functions: list[ParsedFunction] = []
        for match in pattern.finditer(source):
            name = next((g for g in match.groups() if g), "<anonymous>")
            start_line = source[: match.start()].count("\n") + 1
            end_line = min(start_line + 20, len(lines))  # coarse bound in fallback mode
            text = "\n".join(lines[start_line - 1 : end_line])
            functions.append(
                ParsedFunction(
                    id=function_id(file_path, name, start_line),
                    file_path=file_path,
                    language=language,
                    function_name=name,
                    start_line=start_line,
                    end_line=end_line,
                    source_text=text,
                    content_hash=content_hash(text),
                    calls=self._extract_calls(text),
                )
            )
        return functions

    @staticmethod
    def _extract_calls(text: str) -> list[str]:
        """Best-effort extraction of called identifiers for building CALLS edges."""
        calls = set(re.findall(r"(\w+)\s*\(", text))
        keywords = {"if", "for", "while", "switch", "catch", "return", "func", "def", "function"}
        return sorted(calls - keywords)


# Module-level singleton used by the service layer.
_parser: ASTParser | None = None


def get_parser() -> ASTParser:
    global _parser
    if _parser is None:
        _parser = ASTParser()
    return _parser
