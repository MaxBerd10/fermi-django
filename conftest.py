"""
DRF throttling state lives in the cache (Redis), not the database, so it
survives pytest-django's per-test transaction rollback. Without this, tests
across different files that each hit a throttled endpoint (register/login)
accumulate against the same shared limit and start failing each other —
happened for real while adding the throttling tests.
"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """
    Image/Video/Document tests upload real files to real storage (nothing
    here is mocked), so without this they'd write into the project's actual
    media/ directory — accumulating cruft across runs and occasionally
    colliding with a same-named file from a previous run, which Django's
    storage silently renames with a random suffix and breaks any test that
    asserts on the saved filename. Each test gets its own throwaway directory.
    """
    settings.MEDIA_ROOT = tmp_path
