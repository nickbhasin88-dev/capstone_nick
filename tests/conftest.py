import pytest

# the " 2" files (main a33fefb) are macOS duplicates of tomato and shared-base test files; they stay in the repo but
# are not collected (merge decision C8)
collect_ignore_glob = ["* 2.py"]


@pytest.fixture
def ihme_split(monkeypatch):
    """Run with IHME's own program-area split of aid across services (health_model.TREAT_SHARE = None), the rule the
    sudden-cut baseline and the per-service mechanism tests were written for."""
    import health_model as hm
    monkeypatch.setattr(hm, "TREAT_SHARE", None)
