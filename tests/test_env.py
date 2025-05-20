import os
from dotenv import load_dotenv
import yaml
import logging
import pytest
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def substitute_env_vars(obj):
    """Recursively substitute ${VAR} in strings with environment variables."""
    if isinstance(obj, dict):
        return {k: substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(i) for i in obj]
    elif isinstance(obj, str):
        # Substitute ${VAR} with env var
        return re.sub(r'\$\{([^}]+)\}', lambda m: os.getenv(m.group(1), m.group(0)), obj)
    else:
        return obj

def test_env_loading(mock_env_vars, test_config_path):
    """Test environment variable loading and substitution"""
    # Load environment variables
    load_dotenv()
    
    # Check if DISCORD_WEBHOOK_URL is set
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    assert webhook_url is not None, "DISCORD_WEBHOOK_URL is not set"
    assert webhook_url == 'test_webhook_url', "DISCORD_WEBHOOK_URL is not set to expected test value"
    logger.info("✅ DISCORD_WEBHOOK_URL is set correctly")
    
    # Mask the URL for security
    masked_url = webhook_url[:10] + "..." + webhook_url[-10:]
    logger.info(f"Webhook URL (masked): {masked_url}")
    
    # Test config.yml loading
    with open(test_config_path, 'r') as file:
        config = yaml.safe_load(file)
        logger.info("✅ config.yml loaded successfully")
        # Verify webhook URL is using the placeholder
        assert config['discord']['webhook_url'] == '${DISCORD_WEBHOOK_URL}', \
            "config.yml should use environment variable placeholder before substitution"
        # Now test substitution logic
        config_substituted = substitute_env_vars(config)
        assert config_substituted['discord']['webhook_url'] == 'test_webhook_url', \
            "config.yml webhook URL does not match environment variable value after substitution"
        logger.info("✅ config.yml webhook URL matches environment variable value after substitution")

def test_config_without_env_vars(test_config_path):
    """Test config loading without environment variables"""
    # Temporarily unset the environment variable
    if 'DISCORD_WEBHOOK_URL' in os.environ:
        del os.environ['DISCORD_WEBHOOK_URL']
    
    # Load config
    with open(test_config_path, 'r') as file:
        config = yaml.safe_load(file)
        # Verify webhook URL is using the placeholder
        assert config['discord']['webhook_url'] == '${DISCORD_WEBHOOK_URL}', \
            "config.yml is not using environment variable placeholder"
        logger.info("✅ config.yml uses environment variable placeholder when env var is not set")
    # Test substitution logic
    config_substituted = substitute_env_vars(config)
    assert config_substituted['discord']['webhook_url'] == '${DISCORD_WEBHOOK_URL}', \
        "config.yml webhook URL should remain placeholder if env var is not set"
    logger.info("✅ config.yml webhook URL remains placeholder when env var is not set")

if __name__ == "__main__":
    logger.info("Starting environment variable test...")
    if test_env_loading():
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Tests failed!") 