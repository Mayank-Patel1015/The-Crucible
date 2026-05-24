import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cqr import compute_cqr


def test_empty_input_returns_zero():
    result = compute_cqr("", "some ai response")
    assert result["cqr"] == 0.0


def test_cqr_is_in_range():
    result = compute_cqr("From first principles define a perceptron: weighted sum plus sigmoid.", "good")
    assert 0.0 <= result["cqr"] <= 1.0


def test_depth_markers_boost_score():
    shallow = compute_cqr("The answer is yes.", "ok")
    deep = compute_cqr(
        "From first principles, define the axiom, then derive. If we assume X, therefore Y counterexample Z.",
        "ok",
    )
    assert deep["cqr"] > shallow["cqr"]


def test_breakdown_has_required_keys():
    result = compute_cqr("hello world test sentence", "response")
    assert "cqr" in result
    assert "breakdown" in result
    assert {"human_words", "ai_words"} <= result["breakdown"].keys()


def test_word_counts_are_accurate():
    result = compute_cqr("one two three four five", "alpha beta gamma")
    assert result["breakdown"]["human_words"] == 5
    assert result["breakdown"]["ai_words"] == 3
