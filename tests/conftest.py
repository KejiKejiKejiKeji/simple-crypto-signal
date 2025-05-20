import os
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / 'data'

@pytest.fixture
def test_config_path(test_data_dir):
    """Return the path to the test config file."""
    return test_data_dir / 'test_config.yml'

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv('DISCORD_WEBHOOK_URL', 'test_webhook_url') 