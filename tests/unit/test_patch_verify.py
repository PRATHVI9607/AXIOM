"""Property-based verification of patch invariants (PRD §7.6, §12.4) using hypothesis."""
from hypothesis import given, settings
from hypothesis import strategies as st

from axiom.services.patch_service import PATTERNS, PatchCandidate, get_patch_generator

gen = get_patch_generator()

# Code fragments that trigger each pattern, used to fuzz the generator.
TRIGGERS = [
    'q = f"SELECT * FROM t WHERE id={x}"',
    "subprocess.run(c, shell=True)",
    "pickle.loads(b)",
    "open(request.args['f'])",
    'token = "abc123"',
    "d['k'].v",
    "self.n += 1",
]


@settings(max_examples=50, deadline=None)
@given(st.sampled_from(TRIGGERS), st.text(max_size=40))
def test_patch_never_leaves_pattern_verified_true_if_still_vulnerable(trigger, noise):
    """Invariant: a candidate marked verified must NOT still match its risk pattern."""
    code = f"{noise}\n{trigger}\n{noise}"
    for candidate in gen.generate(code):
        rule = next(p for p in PATTERNS if p.name == candidate.pattern)
        if candidate.verified:
            assert not rule.detector.search(candidate.patched)


@settings(max_examples=50, deadline=None)
@given(st.text(max_size=120))
def test_confidence_always_in_unit_interval(code):
    for candidate in gen.generate(code):
        assert 0.0 <= candidate.confidence <= 1.0


@settings(max_examples=50, deadline=None)
@given(st.text(max_size=120))
def test_generate_never_raises(code):
    """API never crashes on arbitrary input (PRD §12.4)."""
    result = gen.generate(code)
    assert isinstance(result, list)
    assert all(isinstance(c, PatchCandidate) for c in result)


def test_patched_differs_from_original():
    """A returned candidate must actually change the code."""
    for trigger in TRIGGERS:
        for c in gen.generate(trigger):
            assert c.patched.strip() != c.original.strip()
