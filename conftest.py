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


@pytest.fixture(autouse=True)
def _public_registration_on_for_tests(settings):
    """Production keeps sign-up closed (settings.PUBLIC_REGISTRATION_ENABLED); the sign-up tests exercise the flow
    itself, and test_registration_closed.py covers the closed default."""
    settings.PUBLIC_REGISTRATION_ENABLED = True


@pytest.fixture(autouse=True)
def _plain_http_for_tests(settings):
    """With DEBUG off (as in CI and production) settings turn SECURE_SSL_REDIRECT on, and the test client talks plain
    http://, so every request would be answered with a 301 to https. In production that redirect is nginx's and
    the Node server's job; here it is switched off so the tests exercise the views."""
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture(autouse=True)
def _static_files_without_a_build_step(settings):
    """Production serves static files through a hashed manifest, which only exists after `collectstatic`. Tests (and CI,
    which never runs collectstatic) must not depend on that build step: plain storage resolves the same URLs."""
    settings.STORAGES = {**settings.STORAGES, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
