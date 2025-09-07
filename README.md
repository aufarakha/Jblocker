# Jblocker - Network Traffic Monitor & Gambling Blocker

Jblocker is a Flask-based network monitoring application that uses machine learning to detect and block gambling websites (judol) in real-time. It monitors network traffic, analyzes HTTP/HTTPS requests, and automatically blocks suspicious gambling-related content.

## Features

### Core Features
- **Real-time Network Monitoring**: Monitors all network connections and traffic
- **Machine Learning Detection**: Uses scikit-learn to classify gambling websites
- **Automatic Blocking**: Blocks detected gambling sites via hosts file modification
- **Web Dashboard**: Modern web interface for monitoring and management
- **SQLite Database**: Stores detection logs, settings, and blocked sites

### Developer Mode
- **Detailed Traffic Logging**: Captures HTTP/HTTPS headers, requests, and responses
- **Proxy Integration**: Uses mitmproxy for deep packet inspection
- **Traffic Analysis**: View all network traffic, not just flagged content
- **Export Functionality**: Export traffic logs for analysis

### Supported Platforms
- Windows

## Installation

### Prerequisites
- Python 3.8 or higher
- Administrator/root privileges (for hosts file modification)

### Quick Setup
1. Clone or download the project
2. Run the setup script:
   ```bash
   python setup.py
   ```
3. Start the application:
   ```bash
   python app.py
   ```
4. Open your browser to `http://localhost:5000`

### Manual Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```

## Usage

### Basic Monitoring
1. Start the application
2. Go to `http://localhost:5000`
3. Click "Toggle Monitor" to start network monitoring
4. View detected gambling sites in the dashboard

### Developer Mode
1. Go to Settings and enable "Developer Mode"
2. Restart monitoring
3. Configure your browser to use `127.0.0.1:8080` as HTTP proxy
4. Visit `http://mitm.it` to install the mitmproxy certificate
5. Browse normally - all traffic will be logged and analyzed

### Configuration
- **Sensitivity**: Adjust ML detection sensitivity (0-100%)
- **Language**: Interface language (English, Indonesian, Spanish)
- **Theme**: Dark/Light/Auto theme
- **Dev Mode**: Enable detailed traffic logging

## Architecture

### Components
- **app.py**: Main Flask application
- **backend/**: Backend modules organized by functionality
  - **core/**: Core system components
    - **database_manager.py**: Database operations and management
  - **ml/**: Machine learning modules
    - **gambling_detector.py**: ML model implementation
    - **model_manager.py**: ML model interface
  - **monitoring/**: Network monitoring modules
    - **traffic_monitor.py**: Network traffic monitoring and analysis
- **templates/**: Web interface templates
- **tests/**: Test scripts and utilities

### Database Schema
- **detection_logs**: ML detection results
- **traffic_logs**: Detailed HTTP/HTTPS traffic (dev mode)
- **settings**: Application configuration
- **blocked_sites**: Manually and automatically blocked sites
- **network_connections**: Real-time connection logs

### Machine Learning
- **Algorithm**: Naive Bayes with TF-IDF vectorization
- **Features**: URL, domain, headers, content analysis
- **Training Data**: Gambling keywords in multiple languages
- **Auto-learning**: Adapts based on user feedback

## API Endpoints

### Monitoring
- `POST /api/toggle_monitoring`: Start/stop monitoring
- `GET /api/stats`: Real-time statistics
- `GET /api/connections`: Active network connections

### Traffic Management
- `POST /api/block_site`: Block a website
- `POST /api/unblock_site`: Unblock a website
- `GET /api/export_blocklist`: Export blocked sites

### Developer Mode
- `GET /api/traffic_logs`: Detailed traffic logs
- `POST /api/cleanup_data`: Clean old data

## Security Considerations

### Permissions Required
- **Administrator/Root**: Required for hosts file modification
- **Network Access**: Required for monitoring network connections
- **Proxy Certificate**: Required for HTTPS traffic analysis (dev mode)

### Privacy
- **Local Processing**: All analysis is done locally
- **No External Calls**: No data sent to external servers
- **Encrypted Storage**: Sensitive data is stored securely
- **User Control**: Users control what data is logged

### Limitations
- **Hosts File**: May conflict with other network tools
- **Proxy Mode**: Requires browser configuration
- **Performance**: May impact system performance during heavy monitoring

## Troubleshooting

### Common Issues

#### "Permission denied" when blocking sites
- **Solution**: Run as administrator/root
- **Windows**: Right-click → "Run as administrator"
- **Linux/macOS**: Use `sudo python app.py`

#### Proxy not working in dev mode
- **Check**: Browser proxy settings (127.0.0.1:8080)
- **Certificate**: Install mitmproxy certificate from http://mitm.it
- **Firewall**: Ensure port 8080 is not blocked

#### High CPU usage
- **Reduce**: Monitoring frequency in settings
- **Disable**: Dev mode if not needed
- **Clean**: Old data regularly

#### False positives/negatives
- **Adjust**: Sensitivity settings
- **Train**: Provide feedback on detections
- **Update**: Keyword lists in the ML model

### Logs and Debugging
- **Application logs**: Check console output
- **Database**: Use SQLite browser to inspect data
- **Network**: Use built-in connection viewer
- **Traffic**: Enable dev mode for detailed analysis

## Development

### Adding New Features
1. **Database**: Update `database_manager.py` for new tables
2. **Monitoring**: Extend `traffic_monitor.py` for new analysis
3. **Web Interface**: Add templates and routes in `app.py`
4. **ML Model**: Update training data in `create_basic_model()`

### Testing
- **Unit Tests**: Test individual components
- **Integration**: Test full monitoring pipeline
- **Performance**: Monitor resource usage
- **Security**: Test privilege escalation

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is for educational and personal use. Please ensure compliance with local laws regarding network monitoring and content filtering.

## Disclaimer

Jblocker is designed to help users monitor and control their network traffic. Users are responsible for:
- Complying with local laws and regulations
- Respecting privacy and terms of service
- Using the tool responsibly and ethically


The developers are not responsible for any misuse of this software.
