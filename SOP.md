# Standard Operating Procedure (SOP) - Simple Crypto Signal Setup on Synology NAS

## Purpose
To establish a standardized procedure for setting up and running the Simple Crypto Signal application on Synology NAS to monitor BTC and ETH with daily signals and Discord notifications.

## Scope
This SOP covers the installation, configuration, and operation of Simple Crypto Signal on Synology NAS for cryptocurrency monitoring.

## Definitions
- **Simple Crypto Signal**: A simplified cryptocurrency signal generator focusing on trend following
- **Synology NAS**: Network Attached Storage device running Synology DSM
- **Discord Webhook**: A method of sending automated messages to a Discord channel
- **SMA/EMA**: Simple Moving Average and Exponential Moving Average technical indicators

## Responsibilities
- System Administrator: Responsible for initial setup and maintenance
- User: Responsible for monitoring signals and responding to alerts

## Procedure

### Prerequisites
1. Synology NAS with DSM 6.0 or later
2. Python 3.9 (Synology Package Center version)
3. Internet connection
4. Access to Synology DSM admin panel
5. Discord webhook URL
6. Basic understanding of cryptocurrency trading

### Steps
1. **Enable SSH on NAS**
   - Open Control Panel in DSM
   - Go to "Terminal & SNMP"
   - Check "Enable SSH service"
   - Click "Apply"
   - Note down your NAS's IP address (shown in Control Panel > Network)

2. **Install Python and Required Packages**
   - Open Package Center in DSM
   - Search for "Python 3.9" (Synology's official package)
   - Install Python 3.9
   - Verify Python installation:
     ```bash
     python3.9 --version
     # Should output: Python 3.9.x
     ```
   - Connect to NAS via SSH:
     - On Windows:
       1. Open PuTTY
       2. Enter your NAS's IP address
       3. Click "Open"
       4. Login with your admin username and password
     - On Mac/Linux:
       1. Open Terminal
       2. Type: `ssh admin@your-nas-ip`
       3. Enter your password when prompted
   - Install pip and required packages:
     ```bash
     # Download get-pip.py
     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
     
     # Install pip
     python3.9 get-pip.py
     
     # Upgrade pip when needed
     python3.9 -m pip install --upgrade pip

     # Install/upgrade yfinance to latest version to handle rate limiting
     python3.9 -m pip install --upgrade yfinance
     
     # Install other requirements
     python3.9 -m pip install -r requirements.txt
     ```

3. **Set Up Application**
   - Create application directory:
     ```bash
     mkdir -p /volume1/crypto-signal
     cd /volume1/crypto-signal
     ```
   - Set proper permissions:
     ```bash
     chmod 755 /volume1/crypto-signal
     ```
   - Clone the repository:
     ```bash
     git clone https://github.com/yourusername/simple-crypto-signal.git .
     ```
   - Create and activate virtual environment:
     ```bash
     python3.9 -m venv /volume1/crypto-signal/venv
     source /volume1/crypto-signal/venv/bin/activate
     python3.9 -m pip install -r requirements.txt
     deactivate
     ```
   - Verify virtual environment:
     ```bash
     ls -l /volume1/crypto-signal/venv/bin/python
     # Should show the Python executable
     ```
   - Configure the application:
     - Create .env file:
       ```bash
       # Create .env file
       touch /volume1/crypto-signal/.env
       
       # Add Discord webhook URL
       echo "DISCORD_WEBHOOK_URL=your_webhook_url_here" >> /volume1/crypto-signal/.env
       
       # Set proper permissions
       chmod 600 /volume1/crypto-signal/.env
       ```
     - Edit config.yml and set the Discord webhook URL to use the environment variable placeholder:
       ```yaml
       webhook_url: ${DISCORD_WEBHOOK_URL}
       ```
     - Ensure webhook URL is properly secured (not exposed in logs)
     - Adjust trading pairs and indicators if needed

4. **Set Up Cron Job on Synology NAS**
   - Open DSM (Synology's web interface)
   - Go to "Control Panel" > "Task Scheduler"
   - Click "Create" > "Scheduled Task" > "User-defined script"
   - Fill in the following details:
     - Task: Crypto Signal Daily
     - User: admin (or your preferred user)
     - Schedule: Daily
     - First run time: 00:00
     - Frequency: Every day
     - Task Settings:
       ```bash
       #!/bin/bash
       cd /volume1/crypto-signal
       
       # Activate virtual environment and run the application
       source /volume1/crypto-signal/venv/bin/activate
       python3.9 crypto_signal.py >> /volume1/crypto-signal/crypto_signal.log 2>&1
       deactivate
       ```
   - Click "OK" to save
   - Right-click the new task and select "Run" to test it
   - Check the log file at `/volume1/crypto-signal/crypto_signal.log` to verify it's working

5. **Verify Setup**
   - Check the terminal output for successful startup
   - Monitor Discord channel for incoming signals
   - Verify signal generation for BTC and ETH
   - Check the application logs for detailed information and troubleshooting

### Log Management
1. **Log Rotation**
   - Set up log rotation to prevent disk space issues:
     ```bash
     # Create logrotate configuration
     sudo nano /etc/logrotate.d/crypto-signal
     ```
   - Add the following configuration:
     ```
     /volume1/crypto-signal/crypto_signal.log {
         daily
         rotate 7
         compress
         delaycompress
         missingok
         notifempty
         create 644 admin admin
     }
     ```

### Troubleshooting
If you encounter any issues:
1. Check SSH connection:
   - Verify SSH is enabled in Control Panel
   - Check if you can ping your NAS's IP address
   - Ensure you're using the correct username and password
2. If pip installation fails:
   - Check if curl is installed: `which curl`
   - If curl is not installed, install it through Package Center
   - Try downloading get-pip.py manually and upload it to your NAS
3. If package installation fails:
   - Check if git is installed: `which git`
   - If git is not installed, install it through Package Center
   - Try installing packages one by one to identify which one fails
4. If you encounter yfinance 429 (Too Many Requests) errors:
   - Check current yfinance version:
     ```bash
     python3.9 -m pip show yfinance
     ```
   - Update to latest version:
     ```bash
     python3.9 -m pip install --upgrade yfinance
     ```
   - Verify the update:
     ```bash
     python3.9 -m pip show yfinance
     ```
   - If issues persist, try adding a delay between requests in your code
5. Check Python version:
   ```bash
   python3.9 --version
   ```
6. Verify installation:
   ```bash
   ls /volume1/crypto-signal/crypto_signal.py
   ```
7. Check the application logs in the terminal
8. Verify the config.yml file permissions
9. If cron job fails:
   - Check the log file at `/volume1/crypto-signal/crypto_signal.log`
   - Verify the Python path is correct
   - Ensure the script has execute permissions
   - Check if the cron job user has access to the application directory
10. If you see import failure, you may not be in virtual env, we can get in by this command on windows.
```
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\venv39\Scripts\Activate.ps1
```

### Security Best Practices
1. Keep Discord webhook URL secure
2. Regularly update Python packages
3. Monitor log files for suspicious activity
4. Use strong passwords for NAS access
5. Regularly backup configuration files

## References
- [Simple Crypto Signal GitHub Repository](https://github.com/yourusername/simple-crypto-signal)
- [Synology Python Documentation](https://www.synology.com/en-global/knowledgebase/DSM/help/DSM/AdminCenter/application_python)

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-03-19 | System Admin | Initial version |
| 1.1 | 2024-03-20 | System Admin | Updated package list, repository URL, and added logging note |
| 1.2 | 2024-03-21 | System Admin | Added detailed cron job setup instructions |
| 1.3 | 2024-03-22 | System Admin | Added security best practices, log management, and verification steps |

## Approval
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |

### Running Tests

- All tests are located in the `tests/` directory.
- To run all tests:
  ```bash
  pytest tests/
  ```
- Ensure your `.env` and `config.yml` are set up as described above for tests to pass. 