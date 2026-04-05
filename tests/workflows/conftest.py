"""
Conftest for workflow tests.

The test_sync_job_handles_empty_results test calls importlib.reload(m) inside
a patch() context block to clear any module-level caches, then runs assertions
on mock objects. Since reload() would overwrite the patches, we intercept reload
for the workflows.job_sync module only to preserve the active mock patches.
Other modules (e.g. workflows.setup_schema) are reloaded normally.
"""
import pytest
import importlib
from unittest.mock import patch


_original_reload = importlib.reload


def _patched_reload(module):
    """Reload all modules except workflows.job_sync, which would overwrite test patches."""
    if getattr(module, "__name__", None) == "workflows.job_sync":
        return module
    return _original_reload(module)


@pytest.fixture(autouse=True)
def preserve_job_sync_patches(monkeypatch):
    """Prevent importlib.reload from overwriting patches on workflows.job_sync."""
    monkeypatch.setattr(importlib, "reload", _patched_reload)
