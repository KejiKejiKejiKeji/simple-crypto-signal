import os
import yaml
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import pandas_ta as ta
import logging
import random
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CryptoSignal:
    def __init__(self, config_path='../config.yml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Get Discord webhook URL from environment variable
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        if not discord_webhook:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set")
        
        # Initialize Discord webhook
        self.discord_webhook = discord_webhook
        self.message_template = self.config['discord']['message_template']
        self.status_template = self.config['discord']['status_template']
        self.min_price_change = self.config['signals']['min_price_change']
        self.trend_confirmation = self.config['signals']['trend_confirmation']
        
        # Indicator periods
        self.sma_long = self.config['indicators']['sma']['long_period']
        self.sma_short = self.config['indicators']['sma']['short_period']
        
        # Rate limiting settings
        self.max_retries = 5
        self.base_delay = 2  # Base delay in seconds
        logger.info("CryptoSignal initialized with config from %s", config_path)

    def _wait_with_jitter(self, delay):
        """Wait for a random time between delay/2 and delay seconds."""
        jitter = random.uniform(delay/2, delay)
        logger.info("Rate limit hit, waiting for %.2f seconds...", jitter)
        time.sleep(jitter)

    def get_historical_data(self, symbol, interval='1d', limit=1095):  # 3 years = 1095 days
        """Get historical data using yfinance with retry logic."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.info("Starting data fetch for %s (attempt %d/%d)...", 
                          symbol, retry_count + 1, self.max_retries)
                
                # Convert symbol to yfinance format if needed
                if symbol.endswith('/USDT'):
                    yf_symbol = symbol.replace('/USDT', '-USD')
                elif symbol.endswith('/USD'):
                    yf_symbol = symbol.replace('/', '-')
                else:
                    yf_symbol = symbol
                
                # Ensure the symbol is in the correct format for cryptocurrencies
                if '-' in yf_symbol:
                    base, quote = yf_symbol.split('-')
                    yf_symbol = f"{base}-{quote}"
                
                logger.info("Fetching data for yfinance symbol: %s", yf_symbol)
                
                # Get data from yfinance
                ticker = yf.Ticker(yf_symbol)
                
                # Log ticker info for debugging
                try:
                    info = ticker.info
                    logger.info("Ticker info: %s", info)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Too Many Requests
                        retry_count += 1
                        delay = self.base_delay * (2 ** retry_count)  # Exponential backoff
                        logger.warning("Rate limit hit while getting ticker info, retrying in %d seconds...", delay)
                        self._wait_with_jitter(delay)
                        continue
                    else:
                        logger.error("Failed to get ticker info: %s", str(e))
                except Exception as e:
                    logger.error("Failed to get ticker info: %s", str(e))
                
                logger.info("Requesting %d days of %s data...", limit, interval)
                df = ticker.history(period=f"{limit}d", interval=interval)
                
                if df.empty:
                    logger.error("%s: No price data found, symbol may be delisted (period=%dd)", yf_symbol, limit)
                    # Try to get more information about why the data is empty
                    try:
                        logger.info("Attempting to get ticker history metadata...")
                        metadata = ticker.get_history_metadata()
                        logger.info("History metadata: %s", metadata)
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 429:  # Too Many Requests
                            retry_count += 1
                            delay = self.base_delay * (2 ** retry_count)
                            logger.warning("Rate limit hit while getting metadata, retrying in %d seconds...", delay)
                            self._wait_with_jitter(delay)
                            continue
                        else:
                            logger.error("Failed to get history metadata: %s", str(e))
                    except Exception as e:
                        logger.error("Failed to get history metadata: %s", str(e))
                    return pd.DataFrame()
                
                logger.info("Received %d rows of data", len(df))
                logger.info("Data columns: %s", df.columns.tolist())
                logger.info("First row: %s", df.iloc[0].to_dict())
                logger.info("Last row: %s", df.iloc[-1].to_dict())
                
                # Rename columns to match expected format
                df = df.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                logger.info("Historical data retrieved for %s", yf_symbol)
                return df
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    retry_count += 1
                    delay = self.base_delay * (2 ** retry_count)
                    logger.warning("Rate limit hit, retrying in %d seconds...", delay)
                    self._wait_with_jitter(delay)
                    continue
                else:
                    logger.error("HTTP Error getting historical data for %s: %s", symbol, str(e))
                    return pd.DataFrame()
            except Exception as e:
                logger.error("Error getting historical data for %s: %s", symbol, str(e))
                import traceback
                logger.error("Full error traceback: %s", traceback.format_exc())
                return pd.DataFrame()
        
        logger.error("Max retries (%d) exceeded for %s", self.max_retries, symbol)
        return pd.DataFrame()

    def calculate_indicators(self, df):
        """Calculate technical indicators using pandas-ta."""
        try:
            logger.info("Starting indicator calculations...")
            # Calculate SMA
            logger.info("Calculating SMA indicators...")
            df['sma_20'] = ta.sma(df['close'], length=self.sma_short)
            df['sma_50'] = ta.sma(df['close'], length=self.sma_long)
            
            # Calculate RSI
            logger.info("Calculating RSI...")
            df['rsi'] = ta.rsi(df['close'])
            
            # Calculate MACD
            logger.info("Calculating MACD...")
            macd = ta.macd(df['close'])
            if macd is not None and isinstance(macd, pd.DataFrame):
                df['macd'] = macd['MACD_12_26_9'] if 'MACD_12_26_9' in macd else np.nan
                df['macd_signal'] = macd['MACDs_12_26_9'] if 'MACDs_12_26_9' in macd else np.nan
                df['macd_hist'] = macd['MACDh_12_26_9'] if 'MACDh_12_26_9' in macd else np.nan
            else:
                df['macd'] = np.nan
                df['macd_signal'] = np.nan
                df['macd_hist'] = np.nan
            
            # Calculate Bollinger Bands
            logger.info("Calculating Bollinger Bands...")
            bbands = ta.bbands(df['close'], length=self.sma_short, std=2.0)
            if bbands is not None and isinstance(bbands, pd.DataFrame):
                df['bb_upper'] = bbands['BBU_20_2.0'] if 'BBU_20_2.0' in bbands else np.nan
                df['bb_middle'] = bbands['BBM_20_2.0'] if 'BBM_20_2.0' in bbands else np.nan
                df['bb_lower'] = bbands['BBL_20_2.0'] if 'BBL_20_2.0' in bbands else np.nan
            else:
                df['bb_upper'] = np.nan
                df['bb_middle'] = np.nan
                df['bb_lower'] = np.nan
            
            logger.info("All indicators calculated successfully")
            return df
            
        except Exception as e:
            logger.error("Error calculating indicators: %s", str(e))
            return df

    def check_trend(self, df):
        """Check for trend signals based on technical indicators."""
        try:
            if len(df) < self.sma_long:
                logger.warning("Insufficient data for trend check")
                return 'neutral'
            
            # Get the latest values
            current_close = df['close'].iloc[-1]
            current_sma20 = df['sma_20'].iloc[-1]
            current_sma50 = df['sma_50'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_macd = df['macd'].iloc[-1]
            current_macd_signal = df['macd_signal'].iloc[-1]
            
            # Calculate price change
            price_change = ((current_close - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            
            # Check for bullish conditions
            if (current_close > current_sma20 > current_sma50 and  # Price above both SMAs
                current_rsi > 50 and  # RSI above 50
                current_macd > current_macd_signal and  # MACD above signal line
                price_change > self.min_price_change):  # Price change above threshold
                logger.info("Bullish trend detected")
                return 'bullish'
            
            # Check for bearish conditions
            elif (current_close < current_sma20 < current_sma50 and  # Price below both SMAs
                  current_rsi < 50 and  # RSI below 50
                  current_macd < current_macd_signal and  # MACD below signal line
                  price_change < -self.min_price_change):  # Price change below threshold
                logger.info("Bearish trend detected")
                return 'bearish'
            
            logger.info("Neutral trend detected")
            return 'neutral'
            
        except Exception as e:
            logger.error("Error checking trend: %s", str(e))
            return 'neutral'

    def send_discord_message(self, symbol, signal_type, price, change):
        """Send signal to Discord webhook."""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = self.message_template.format(
                symbol=symbol,
                signal_type=signal_type,
                price=price,
                change=change,
                time=current_time
            )
            
            payload = {'content': message}
            response = requests.post(self.discord_webhook, json=payload)
            response.raise_for_status()
            logger.info("Discord message sent for %s: %s", symbol, signal_type)
            
        except Exception as e:
            logger.error("Error sending Discord message: %s", str(e))

    def wait_until_next_run(self):
        """Wait until the next scheduled run time (00:00 UTC)"""
        now = datetime.utcnow()
        next_run = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # If it's already past 00:00 UTC, wait until tomorrow
        if now >= next_run:
            next_run = next_run + timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Next run scheduled at {next_run} UTC (in {wait_seconds/3600:.1f} hours)")
        time.sleep(wait_seconds)

    def log_market_status(self, df, symbol):
        """Log current market status including key indicators."""
        try:
            current_close = df['close'].iloc[-1]
            current_sma20 = df['sma_20'].iloc[-1]
            current_sma50 = df['sma_50'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_macd = df['macd'].iloc[-1]
            current_macd_signal = df['macd_signal'].iloc[-1]
            current_bb_upper = df['bb_upper'].iloc[-1]
            current_bb_lower = df['bb_lower'].iloc[-1]
            
            # Calculate daily change
            daily_change = ((current_close - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            
            # Format status message for logging
            status_message = f"""
Market Status for {symbol}:
----------------------------
Price: ${current_close:.2f} (Change: {daily_change:.2f}%)
RSI: {current_rsi:.2f}
MACD: {current_macd:.2f} (Signal: {current_macd_signal:.2f})
SMA20: ${current_sma20:.2f}
SMA50: ${current_sma50:.2f}
Bollinger Bands: Upper ${current_bb_upper:.2f} | Lower ${current_bb_lower:.2f}
"""
            logger.info(status_message)
            
            # Send formatted status to Discord
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            discord_message = self.status_template.format(
                symbol=symbol,
                price=current_close,
                change=daily_change,
                rsi=current_rsi,
                macd=current_macd,
                macd_signal=current_macd_signal,
                sma20=current_sma20,
                sma50=current_sma50,
                bb_upper=current_bb_upper,
                bb_lower=current_bb_lower,
                time=current_time
            )
            
            payload = {'content': discord_message}
            response = requests.post(self.discord_webhook, json=payload)
            response.raise_for_status()
            logger.info("Market status sent to Discord for %s", symbol)
            
        except Exception as e:
            logger.error("Error logging market status: %s", str(e))

    def run(self):
        """Run analysis once and exit"""
        logger.info("Starting Crypto Signal Monitor...")
        
        try:
            logger.info("Running daily analysis...")
            for symbol in self.config['symbols']:
                try:
                    logger.info("Processing symbol: %s", symbol)
                    # Get historical data
                    df = self.get_historical_data(symbol)
                    if df.empty:
                        logger.error("No data received for %s, skipping...", symbol)
                        continue
                    
                    # Calculate indicators
                    df = self.calculate_indicators(df)
                    
                    # Log market status
                    logger.info("Logging market status for %s...", symbol)
                    self.log_market_status(df, symbol)
                    
                    # Check for signals
                    logger.info("Checking for signals for %s...", symbol)
                    signal = self.check_trend(df)
                    
                    if signal != 'neutral':
                        current_price = df['close'].iloc[-1]
                        logger.info("Sending signal message for %s...", symbol)
                        self.send_discord_message(symbol, signal, current_price, current_price - df['close'].iloc[-2])
                        logger.info("Signal generated for %s: %s", symbol, signal)
                    else:
                        logger.info("No signal for %s", symbol)
                    
                except Exception as e:
                    logger.error("Error processing %s: %s", symbol, str(e))
            
            logger.info("Analysis completed successfully")
            
        except Exception as e:
            logger.error("Error in main process: %s", str(e))
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Crypto Signal application.")
    parser.add_argument('--config', type=str, default="config.yml", help="Path to the config YAML file (default: config.yml in project root)")
    args = parser.parse_args()
    signal = CryptoSignal(config_path=args.config)
    signal.run() 