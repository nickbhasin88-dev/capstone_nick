import pytest


@pytest.fixture
def ihme_split(monkeypatch):
    """Run with IHME's own program-area split of aid across services (health_model.TREAT_SHARE = None), the rule the
    sudden-cut baseline and the per-service mechanism tests were written for."""
    import health_model as hm
    monkeypatch.setattr(hm, "TREAT_SHARE", None)
