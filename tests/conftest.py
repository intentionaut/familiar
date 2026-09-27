"""Every test starts with no house in the environment.

A writer's shell often sets these. Left in, a test that forgets to pass its own
folder reads the real vault: it fails on the writer's pieces, or passes on them,
and CI (which has no house) never sees the difference. A test that wants a
house sets one itself.
"""
import pytest

HOUSE_VARS = ("FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG", "FAMILIAR_PIECES")


@pytest.fixture(autouse=True)
def no_house_from_the_shell(monkeypatch):
    for var in HOUSE_VARS:
        monkeypatch.delenv(var, raising=False)
