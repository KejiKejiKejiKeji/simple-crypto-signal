import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_signal import CryptoSignal

@pytest.fixture
def test_config():
    return {
        'discord': {
            'message_template': '🚨 {symbol} {signal_type} Signal\nPrice: {price}\nChange: {change}%\nTime: {time}',
            'status_template': 'Market Status for {symbol}:\n----------------------------\nPrice: ${price:.2f} (Change: {change:.2f}%)\nRSI: {rsi:.2f}\nMACD: {macd:.2f} (Signal: {macd_signal:.2f})\nSMA20: ${sma20:.2f}\nSMA50: ${sma50:.2f}\nBollinger Bands: Upper ${bb_upper:.2f} | Lower ${bb_lower:.2f}\nTime: {time}',
            'webhook_url': 'https://discord.com/api/webhooks/test'
        },
        'indicators': {
            'sma': {
                'long_period': 50,
                'short_period': 20
            }
        },
        'signals': {
            'min_price_change': 2.0,
            'trend_confirmation': 3
        }
    }

@pytest.fixture
def mock_yfinance():
    with patch('crypto_signal.yf.Ticker') as mock_ticker:
        # Create a mock instance
        ticker_instance = Mock()
        
        # Create mock historical data
        mock_data = pd.DataFrame({
            'Open': [35000.0, 35050.0, 35150.0],
            'High': [35100.0, 35200.0, 35300.0],
            'Low': [34900.0, 35000.0, 35100.0],
            'Close': [35050.0, 35150.0, 35250.0],
            'Volume': [100.0, 150.0, 200.0]
        }, index=pd.date_range(start='2024-01-01', periods=3, freq='1H'))
        
        ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = ticker_instance
        
        yield ticker_instance

@pytest.fixture
def signal(test_config, tmp_path, mock_yfinance):
    # Create a temporary config file for testing
    config_path = tmp_path / "test_config.yml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(test_config, f)
    
    return CryptoSignal(config_path=str(config_path))

def test_get_historical_data(signal):
    # Test data retrieval
    df = signal.get_historical_data('BTC-USD', '1h', 100)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'close' in df.columns
    assert len(df) > 0

def test_calculate_indicators(signal):
    # Test indicator calculation with more realistic, noisy data
    n = 100  # Increased number of data points to ensure enough for all indicators
    np.random.seed(42)
    base = np.linspace(100, 120, n)
    noise = np.random.normal(0, 2, n)
    close = base + 5 * np.sin(np.linspace(0, 6 * np.pi, n)) + noise
    df = pd.DataFrame({
        'close': close,
        'high': close + np.random.uniform(1, 3, n),
        'low': close - np.random.uniform(1, 3, n),
        'volume': np.random.randint(1000, 5000, n)
    })
    
    result = signal.calculate_indicators(df)
    assert isinstance(result, pd.DataFrame)
    assert 'sma_20' in result.columns
    assert 'sma_50' in result.columns
    assert 'rsi' in result.columns
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'macd_hist' in result.columns
    assert 'bb_upper' in result.columns
    assert 'bb_middle' in result.columns
    assert 'bb_lower' in result.columns
    
    # Verify that at least one non-NaN value exists in each indicator column
    assert result['sma_20'].notna().any(), "SMA 20 has no valid values"
    assert result['sma_50'].notna().any(), "SMA 50 has no valid values"
    assert result['rsi'].notna().any(), "RSI has no valid values"
    assert result['macd'].notna().any(), "MACD has no valid values"
    assert result['macd_signal'].notna().any(), "MACD signal has no valid values"
    assert result['macd_hist'].notna().any(), "MACD histogram has no valid values"
    assert result['bb_upper'].notna().any(), "Bollinger Bands upper has no valid values"
    assert result['bb_middle'].notna().any(), "Bollinger Bands middle has no valid values"
    assert result['bb_lower'].notna().any(), "Bollinger Bands lower has no valid values"
    
    # Verify that the indicators have reasonable values
    assert result['sma_20'].mean() > 0, "SMA 20 mean should be positive"
    assert result['sma_50'].mean() > 0, "SMA 50 mean should be positive"
    assert result['rsi'].mean() > 0 and result['rsi'].mean() < 100, "RSI should be between 0 and 100"
    assert result['bb_upper'].mean() > result['bb_middle'].mean(), "BB upper should be above middle"
    assert result['bb_middle'].mean() > result['bb_lower'].mean(), "BB middle should be above lower"

def test_check_trend(signal):
    # Test trend checking
    df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104],
        'sma_20': [98, 99, 100, 101, 102],
        'sma_50': [95, 96, 97, 98, 99],
        'rsi': [60, 65, 70, 75, 80],
        'macd': [1, 2, 3, 4, 5],
        'macd_signal': [0, 1, 2, 3, 4],
        'macd_hist': [1, 1, 1, 1, 1],
        'bb_upper': [110, 111, 112, 113, 114],
        'bb_middle': [100, 101, 102, 103, 104],
        'bb_lower': [90, 91, 92, 93, 94]
    })
    
    trend = signal.check_trend(df)
    assert isinstance(trend, str)
    assert trend in ['bullish', 'bearish', 'neutral']

@patch('crypto_signal.requests.post')
def test_send_discord_message(mock_post, signal):
    # Test Discord message sending
    mock_post.return_value.status_code = 204
    
    signal.send_discord_message('BTC-USD', 'bullish', 50000, 2.5)
    
    # Verify the request was made with correct data
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['json']['content'] is not None
    assert 'BTC-USD' in kwargs['json']['content']
    assert 'bullish' in kwargs['json']['content']
    assert '50000' in kwargs['json']['content']
    assert '2.5' in kwargs['json']['content'] 