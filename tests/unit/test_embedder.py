"""Unit tests for the embedding engine's fallback + prompt building (PRD §7.2)."""
import pytest

from axiom.services.embed_service import Embedder


def test_fallback_embedding_is_deterministic_and_bounded():
    a = Embedder._embed_fallback("hello world")
    b = Embedder._embed_fallback("hello world")
    assert a == b
    assert len(a) == 768
    assert all(-1.0 <= v <= 1.0 for v in a)


def test_fallback_differs_by_input():
    assert Embedder._embed_fallback("a") != Embedder._embed_fallback("b")


def test_prompt_includes_context():
    e = Embedder()
    prompt = e.build_prompt("def f(): pass", "x.py", "python", ["caller_a"])
    assert "x.py" in prompt and "python" in prompt and "caller_a" in prompt


def test_long_function_prompt_truncated():
    e = Embedder()
    src = "\n".join(f"line{i}" for i in range(200))
    prompt = e.build_prompt(src, "x.py", "python", [])
    assert "truncated" in prompt


@pytest.mark.asyncio
async def test_embed_text_falls_back_when_provider_down():
    # Default provider is ollama; nothing is listening in tests, so it must fall back.
    e = Embedder()
    vec = await e.embed_text("some code")
    assert len(vec) == 768


@pytest.mark.asyncio
async def test_embed_batch_returns_one_vector_each():
    e = Embedder()
    vecs = await e.embed_batch(["a", "b", "c"])
    assert len(vecs) == 3 and all(len(v) == 768 for v in vecs)
