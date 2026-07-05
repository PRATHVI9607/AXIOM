"""Patch generator & lightweight verifier (PRD §7.6).

Detects the 7 supported vulnerability patterns and produces candidate patches.
LLM-based rewriting is optional; deterministic template patches ship by default
so the feature works fully offline and is unit-testable.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class PatchCandidate:
    pattern: str
    original: str
    patched: str
    confidence: float
    verified: bool = False
    test_results: dict[str, int] | None = None


# ── Pattern detectors: (name, regex, patcher) ────────────
def _patch_sql_injection(code: str) -> str:
    # f-string / concatenated SQL → parameterized placeholder.
    patched = re.sub(
        r'(["\'])SELECT .*?\{(\w+)\}.*?\1',
        r"'SELECT ... WHERE col = ?'  # bind (\2,)",
        code,
    )
    return patched.replace("f'", "'").replace('f"', '"')


def _patch_command_injection(code: str) -> str:
    patched = code.replace("shell=True", "shell=False")
    patched = re.sub(r"os\.system\((.*?)\)", r"subprocess.run([\1], shell=False, check=True)", patched)
    return patched


def _patch_deserialization(code: str) -> str:
    patched = code.replace("pickle.loads", "json.loads")
    patched = re.sub(r"yaml\.load\(([^,)]+)\)", r"yaml.safe_load(\1)", patched)
    return patched


def _patch_path_traversal(code: str) -> str:
    return re.sub(
        r"open\(([^)]+)\)",
        r"open(os.path.realpath(os.path.join(SAFE_ROOT, os.path.basename(\1))))",
        code,
    )


def _patch_hardcoded_secret(code: str) -> str:
    return re.sub(
        r'(password|secret|token|api_key)\s*=\s*["\'][^"\']+["\']',
        r'\1 = os.environ["\1".upper()]',
        code,
        flags=re.IGNORECASE,
    )


def _patch_unchecked_null(code: str) -> str:
    return "# guard added by AXIOM\nif value is None:\n    raise ValueError('value must not be None')\n" + code


def _patch_race_condition(code: str) -> str:
    return "with _axiom_lock:  # mutex inserted by AXIOM\n    " + code.replace("\n", "\n    ")


@dataclass
class PatternRule:
    name: str
    detector: re.Pattern[str]
    patcher: Callable[[str], str]
    confidence: float


# Detectors are tuned to minimise false positives (PRD's <25% FP target). Each
# requires the risk to appear in a real code construct, not just a keyword —
# e.g. SQL only inside an interpolated string, `shell=True` case-sensitive, a
# credential literal that is not a URL.
PATTERNS: list[PatternRule] = [
    # SQL keyword interpolated into an f-string/format alongside a SQL clause.
    PatternRule(
        "sql_injection",
        re.compile(
            r"f['\"][^'\"]*\b(SELECT|INSERT|UPDATE|DELETE)\b[^'\"]*\b(FROM|INTO|SET|WHERE)\b"
            r"|['\"][^'\"]*\b(SELECT|INSERT|UPDATE|DELETE)\b[^'\"]*['\"]\s*[+%]\s*\w",
            re.IGNORECASE,
        ),
        _patch_sql_injection,
        0.82,
    ),
    # Case-sensitive: real Python is shell=True (capital T), not the string "shell=true".
    PatternRule(
        "command_injection",
        re.compile(r"shell\s*=\s*True|\bos\.system\(|\bsubprocess\.call\([^)]*shell\s*=\s*True"),
        _patch_command_injection,
        0.85,
    ),
    PatternRule(
        "deserialization",
        re.compile(r"pickle\.loads|yaml\.load\((?!.*Loader)", re.IGNORECASE),
        _patch_deserialization,
        0.8,
    ),
    PatternRule(
        "path_traversal",
        re.compile(r"open\([^)]*(\.\.|request\.|input\(|argv)", re.IGNORECASE),
        _patch_path_traversal,
        0.7,
    ),
    # Credential var assigned a short literal that is NOT a URL.
    PatternRule(
        "hardcoded_credentials",
        re.compile(
            r"\b\w*(password|passwd|secret|api_key|apikey|token)\w*\s*=\s*"
            r"['\"](?!https?://)[^'\"\s]{6,}['\"]",
            re.IGNORECASE,
        ),
        _patch_hardcoded_secret,
        0.78,
    ),
    PatternRule(
        "unchecked_null",
        re.compile(r"\.get\([^)]*\)\.\w+|\[\s*['\"]\w+['\"]\s*\]\.\w+"),
        _patch_unchecked_null,
        0.6,
    ),
    # Conservative: shared instance-attribute mutation (classic race), not every
    # `+= 1` counter or `threading.` import.
    PatternRule(
        "race_condition",
        re.compile(r"self\.\w+\s*\+=|global\s+\w+\s*\n\s*\w+\s*="),
        _patch_race_condition,
        0.55,
    ),
]


class PatchGenerator:
    """Detects risk patterns and emits verified patch candidates."""

    def detect_patterns(self, code: str) -> list[str]:
        return [rule.name for rule in PATTERNS if rule.detector.search(code)]

    def generate(self, code: str) -> list[PatchCandidate]:
        """Return one patch candidate per detected pattern, verified heuristically."""
        candidates: list[PatchCandidate] = []
        for rule in PATTERNS:
            if not rule.detector.search(code):
                continue
            try:
                patched = rule.patcher(code)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Patcher for %s failed: %s", rule.name, exc)
                continue
            if patched.strip() == code.strip():
                continue
            candidate = PatchCandidate(
                pattern=rule.name,
                original=code,
                patched=patched,
                confidence=rule.confidence,
            )
            candidate.verified, candidate.test_results = self._verify(rule, patched)
            candidates.append(candidate)
        return candidates

    def _verify(self, rule: PatternRule, patched: str) -> tuple[bool, dict[str, int]]:
        """Lightweight invariant check: patched code no longer matches the risk pattern."""
        still_vulnerable = bool(rule.detector.search(patched))
        passed = 0 if still_vulnerable else 1
        return (not still_vulnerable), {"passed": passed, "failed": int(still_vulnerable)}


_generator: PatchGenerator | None = None


def get_patch_generator() -> PatchGenerator:
    global _generator
    if _generator is None:
        _generator = PatchGenerator()
    return _generator
