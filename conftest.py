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
