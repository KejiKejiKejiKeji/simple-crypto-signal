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
     
     # Now install the required packages
     python3.9 -m pip install --upgrade pip
     python3.9 -m pip install pandas numpy requests python-binance ta-lib python-dotenv
     ```

3. **Set Up Application**
   - Create application directory:
     ```bash
     mkdir -p /volume1/crypto-signal
     cd /volume1/crypto-signal
     ```
   - Clone the repository:
     ```bash
     git clone https://github.com/yourusername/simple-crypto-signal.git .
     ```
   - Configure the application:
     - Edit config.yml and update the Discord webhook URL
     - Adjust trading pairs and indicators if needed

4. **Run Crypto Signal**
   - Connect to NAS via SSH
   - Navigate to the application directory:
     ```bash
     cd /volume1/crypto-signal
     ```
   - Run the application:
     ```bash
     python3.9 crypto_signal.py
     ```

5. **Set Up Auto-Start**
   - Open Control Panel in DSM
   - Go to Task Scheduler
   - Create a new Scheduled Task
   - Set the following:
     - Task: User-defined script
     - User: admin
     - Schedule: At startup
     - Task Settings:
       ```bash
       cd /volume1/crypto-signal && python3.9 crypto_signal.py
       ```

6. **Verify Setup**
   - Check the terminal output for successful startup
   - Monitor Discord channel for incoming signals
   - Verify signal generation for BTC and ETH

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
4. Check Python version:
   ```bash
   python3.9 --version
   ```
5. Verify installation:
   ```bash
   ls /volume1/crypto-signal/crypto_signal.py
   ```
6. Check the application logs in the terminal
7. Verify the config.yml file permissions

## References
- [Simple Crypto Signal GitHub Repository](https://github.com/yourusername/simple-crypto-signal)
- [Synology Python Documentation](https://www.synology.com/en-global/knowledgebase/DSM/help/DSM/AdminCenter/application_python)

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-03-19 | System Admin | Initial version |

## Approval
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | | 