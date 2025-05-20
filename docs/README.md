# Simple Crypto Signal

A simplified cryptocurrency signal generator that focuses on trend following strategy and sends notifications to Discord.

## Features

- Monitors BTC and ETH prices on Binance
- Uses SMA and EMA for trend following
- Sends signals to Discord webhook
- Configurable through YAML file
- Easy to install and run on Synology NAS

## Installation

1. Clone the repository:
```bash
git clone https://github.com/KejiKejiKejiKeji/simple-crypto-signal.git
cd simple-crypto-signal
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
- Copy `config.yml` and update as needed. For the Discord webhook, use:
  ```yaml
  webhook_url: ${DISCORD_WEBHOOK_URL}
  ```
- Create a `.env` file in the project root:
  ```
  DISCORD_WEBHOOK_URL=your_actual_webhook_url_here
  ```
- Adjust trading pairs and indicators as needed

## Usage

Run the application:
```bash
python src/crypto_signal.py
```

The application will:
- Monitor configured trading pairs
- Calculate technical indicators
- Generate signals based on trend following strategy
- Send notifications to Discord

## Configuration

Edit `config.yml` to customize:
- Trading pairs
- Timeframe
- Technical indicators
- Signal thresholds
- Discord webhook settings (use `${DISCORD_WEBHOOK_URL}` as a placeholder)

Sensitive information (like the Discord webhook URL) should be stored in the `.env` file, which is already included in `.gitignore`.

## Running Tests

All tests are located in the `tests/` directory. To run all tests:
```bash
pytest tests/
```

## Running on Synology NAS

See the [SOP.md](SOP.md) file for detailed instructions on setting up and running the application on Synology NAS. 