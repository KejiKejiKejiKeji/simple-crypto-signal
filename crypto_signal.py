import os
import yaml
import time
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from binance.client import Client
import talib

class CryptoSignal:
    def __init__(self, config_path='config.yml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize Binance client
        self.client = Client()
        
        # Initialize Discord webhook
        self.webhook_url = self.config['discord']['webhook_url']
        self.message_template = self.config['discord']['message_template']

    def get_historical_data(self, symbol, timeframe):
        """Fetch historical klines/candlestick data from Binance"""
        klines = self.client.get_klines(
            symbol=symbol,
            interval=timeframe,
            limit=100  # Get last 100 candles
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        return df

    def calculate_indicators(self, df):
        """Calculate technical indicators for trend following"""
        # Calculate SMAs
        df['sma_short'] = talib.SMA(df['close'], timeperiod=self.config['indicators']['sma']['short_period'])
        df['sma_long'] = talib.SMA(df['close'], timeperiod=self.config['indicators']['sma']['long_period'])
        
        # Calculate EMAs
        df['ema_short'] = talib.EMA(df['close'], timeperiod=self.config['indicators']['ema']['short_period'])
        df['ema_long'] = talib.EMA(df['close'], timeperiod=self.config['indicators']['ema']['long_period'])
        
        return df

    def check_trend(self, df):
        """Check for trend following signals"""
        # Get the last few candles
        last_candles = df.tail(self.config['signals']['trend_confirmation'])
        
        # Check SMA trend
        sma_trend = all(last_candles['sma_short'] > last_candles['sma_long'])
        
        # Check EMA trend
        ema_trend = all(last_candles['ema_short'] > last_candles['ema_long'])
        
        # Calculate price change
        price_change = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        
        # Determine signal
        if sma_trend and ema_trend and price_change > self.config['signals']['min_price_change']:
            return 'BUY', price_change
        elif not sma_trend and not ema_trend and price_change < -self.config['signals']['min_price_change']:
            return 'SELL', price_change
        return None, price_change

    def send_discord_message(self, symbol, signal_type, price, change):
        """Send signal to Discord webhook"""
        message = self.message_template.format(
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            change=change,
            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        try:
            response = requests.post(self.webhook_url, json={'content': message})
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending Discord message: {e}")

    def run(self):
        """Main loop to check for signals"""
        print("Starting Crypto Signal Monitor...")
        
        while True:
            for symbol in self.config['symbols']:
                try:
                    # Get historical data
                    df = self.get_historical_data(symbol, self.config['timeframe'])
                    
                    # Calculate indicators
                    df = self.calculate_indicators(df)
                    
                    # Check for signals
                    signal, price_change = self.check_trend(df)
                    
                    if signal:
                        current_price = df['close'].iloc[-1]
                        self.send_discord_message(symbol, signal, current_price, price_change)
                        print(f"Signal generated for {symbol}: {signal}")
                    
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
            
            # Wait for 1 hour before next check
            time.sleep(3600)

if __name__ == "__main__":
    signal = CryptoSignal()
    signal.run() 