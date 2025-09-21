from aurweb import defaults


def test_fallback_pp() -> None:
    assert defaults.fallback_pp(75) == defaults.PP
    assert defaults.fallback_pp(100) == 100


def test_pp() -> None:
    assert defaults.PP == 50


def test_o() -> None:
    assert defaults.O == 0
