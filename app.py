from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import json
import threading
import time
import os
import requests
import socket
import psutil
from urllib.parse import urlparse
import re

# Import backend modules
from backend.core.database_manager import DatabaseManager
from backend.monitoring.traffic_monitor import NetworkTrafficMonitor
from backend.ml import model_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize components
db_manager = DatabaseManager()
traffic_monitor = None

# Initialize default settings
def init_default_settings():
    """Initialize default settings if they don't exist"""
    defaults = {
        'sensitivity': '50',
        'language': 'English',
        'theme': 'Dark',
        'monitoring_enabled': 'true',
        'dev_mode': 'false'
    }
    
    for key, value in defaults.items():
        if not db_manager.get_setting(key):
            db_manager.set_setting(key, value)

def init_ml_model():
    """Initialize or load the machine learning model"""
    global traffic_monitor
    
    # Initialize ML model with database manager
    success = model_manager.init_ml_model(db_manager)
    
    if success:
        print("✓ ML model initialized successfully")
    else:
        print("✗ Failed to initialize ML model")
    
    # Initialize traffic monitor with ML model
    traffic_monitor = NetworkTrafficMonitor(db_manager, model_manager.predict_gambling)

# ML prediction functions are now in ml_model.py

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    # Get statistics from database manager
    stats = db_manager.get_statistics()
    print(f"Debug - Raw stats from database: {stats}")  # Debug output
    
    # Get recent detections
    recent_detections = db_manager.get_detections(limit=10)
    print(f"Debug - Recent detections count: {len(recent_detections)}")  # Debug output
    
    # Get monitoring status
    monitoring_enabled = db_manager.get_setting('monitoring_enabled') == 'true'
    
    # Add real-time stats if traffic monitor is available
    if traffic_monitor:
        real_time_stats = traffic_monitor.get_real_time_stats()
        stats.update(real_time_stats)
        print(f"Debug - After adding real-time stats: {stats}")  # Debug output
    
    stats.update({
        'status': 'Secure' if stats.get('blocked_count', 0) < 10 else 'Alert',
        'monitoring_enabled': monitoring_enabled,
        'total_connections': stats.get('total_detections', 0),  # Map to template key
        'blocked_sites': stats.get('blocked_count', 0)  # Map to template key
    })
    
    print(f"Debug - Final stats sent to template: {stats}")  # Debug output
    
    return render_template('index.html', stats=stats, recent_detections=recent_detections)

@app.route('/details')
def details():
    """Detailed detection logs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Get detections from database manager
    offset = (page - 1) * 20
    detections_list = db_manager.get_detections(limit=20, offset=offset, search=search)
    
    # Create a simple pagination object
    class SimplePagination:
        def __init__(self, items, page, per_page):
            self.items = items
            self.page = page
            self.per_page = per_page
    
    detections = SimplePagination(detections_list, page, 20)
    
    return render_template('details.html', detections=detections, search=search)

@app.route('/dev_traffic')
def dev_traffic():
    """Developer mode - detailed traffic logs"""
    # Check if dev mode is enabled
    dev_mode = db_manager.get_setting('dev_mode') == 'true'
    if not dev_mode:
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    hours = request.args.get('hours', 24, type=int)
    
    # Get traffic logs
    offset = (page - 1) * 50
    traffic_logs = db_manager.get_traffic_logs(limit=50, offset=offset, hours=hours)
    
    return render_template('dev_traffic.html', traffic_logs=traffic_logs, hours=hours)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page"""
    if request.method == 'POST':
        # Update settings
        for key in ['sensitivity', 'language', 'theme', 'dev_mode']:
            value = request.form.get(key)
            if value is not None:
                db_manager.set_setting(key, value)
        
        # Handle dev mode toggle
        dev_mode = request.form.get('dev_mode') == 'on'
        db_manager.set_setting('dev_mode', 'true' if dev_mode else 'false')
        
        return redirect(url_for('settings'))
    
    # Get current settings
    current_settings = {
        'sensitivity': db_manager.get_setting('sensitivity') or '50',
        'language': db_manager.get_setting('language') or 'English',
        'theme': db_manager.get_setting('theme') or 'Dark',
        'dev_mode': db_manager.get_setting('dev_mode') or 'false'
    }
    
    # Get statistics
    stats = db_manager.get_statistics()
    blocked_sites = db_manager.get_blocked_sites()
    
    stats.update({
        'total_blocked': len(blocked_sites),
        'accuracy': 98.5  # Placeholder - calculate based on user feedback
    })
    
    return render_template('settings.html', settings=current_settings, stats=stats)

# API Routes
@app.route('/api/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    """Toggle network monitoring on/off"""
    global traffic_monitor
    
    data = request.get_json()
    enable = data.get('enable', False)
    dev_mode = data.get('dev_mode', False) or db_manager.get_setting('dev_mode') == 'true'
    
    if enable and traffic_monitor:
        success = traffic_monitor.start_monitoring(dev_mode=dev_mode)
        if success:
            db_manager.set_setting('monitoring_enabled', 'true')
            return jsonify({'success': True, 'monitoring_active': True, 'dev_mode': dev_mode})
    elif not enable and traffic_monitor:
        traffic_monitor.stop_monitoring()
        db_manager.set_setting('monitoring_enabled', 'false')
        return jsonify({'success': True, 'monitoring_active': False})
    
    return jsonify({'success': False, 'error': 'Traffic monitor not available'})

@app.route('/api/block_site', methods=['POST'])
def block_site():
    """Manually block a website"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        domain = urlparse(url).netloc
        if traffic_monitor:
            success = traffic_monitor.block_domain(domain)
        else:
            success = db_manager.add_blocked_site(url, "Manually blocked")
        
        if success:
            return jsonify({'success': True, 'message': f'Blocked {url}'})
        else:
            return jsonify({'error': 'Failed to block website'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/unblock_site', methods=['POST'])
def unblock_site():
    """Unblock a website"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        domain = urlparse(url).netloc
        if traffic_monitor:
            success = traffic_monitor.unblock_domain(domain)
        else:
            success = db_manager.remove_blocked_site(url)
        
        if success:
            return jsonify({'success': True, 'message': f'Unblocked {url}'})
        else:
            return jsonify({'error': 'Failed to unblock website'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train_model', methods=['POST'])
def train_model():
    """Retrain the ML model with user feedback"""
    data = request.get_json()
    url = data.get('url')
    is_gambling = data.get('is_gambling', False)
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        # Add training feedback to the ML model
        success = model_manager.add_training_feedback(url, is_gambling)
        
        if success:
            return jsonify({'success': True, 'message': 'Training feedback recorded'})
        else:
            return jsonify({'error': 'Failed to record feedback'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get real-time statistics"""
    try:
        # Get statistics from database manager
        stats = db_manager.get_statistics()
        
        # Add real-time monitoring stats
        if traffic_monitor:
            real_time_stats = traffic_monitor.get_real_time_stats()
            stats.update(real_time_stats)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/traffic_logs')
def get_traffic_logs():
    """Get traffic logs for dev mode"""
    dev_mode = db_manager.get_setting('dev_mode') == 'true'
    if not dev_mode:
        return jsonify({'error': 'Dev mode not enabled'}), 403
    
    try:
        hours = request.args.get('hours', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        traffic_logs = db_manager.get_traffic_logs(limit=limit, hours=hours)
        
        return jsonify({
            'traffic_logs': traffic_logs,
            'count': len(traffic_logs)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections')
def get_connections():
    """Get active network connections"""
    try:
        connections = db_manager.get_connections(limit=50)
        return jsonify({
            'connections': connections,
            'count': len(connections)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_blocklist')
def export_blocklist():
    """Export blocked sites list"""
    try:
        blocked_sites_list = db_manager.get_blocked_sites()
        
        return jsonify({
            'blocked_sites': blocked_sites_list,
            'export_date': datetime.utcnow().isoformat(),
            'total_count': len(blocked_sites_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup_data', methods=['POST'])
def cleanup_data():
    """Clean up old data"""
    try:
        days = request.get_json().get('days', 30)
        db_manager.cleanup_old_data(days)
        return jsonify({'success': True, 'message': f'Cleaned data older than {days} days'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bandwidth_history')
def get_bandwidth_history():
    """Get bandwidth usage history for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if traffic_monitor:
            history = traffic_monitor.get_bandwidth_history(hours)
        else:
            # Fallback data if traffic monitor not available
            history = []
        
        return jsonify({
            'bandwidth_history': history,
            'hours': hours
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model_info')
def get_model_info():
    """Get ML model information"""
    try:
        model_info = model_manager.get_model_info()
        return jsonify(model_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections_history')
def get_connections_history():
    """Get connection attempts history for charts"""
    try:
        hours = request.args.get('hours', 12, type=int)
        
        # Get connection logs from database
        connections = db_manager.get_connections(limit=1000)
        
        # Group connections by hour
        from collections import defaultdict
        hourly_data = defaultdict(int)
        
        current_time = datetime.now()
        
        for conn in connections:
            if conn.get('timestamp'):
                try:
                    conn_time = datetime.fromisoformat(conn['timestamp'])
                    # Only include connections from the last X hours
                    if (current_time - conn_time).total_seconds() <= hours * 3600:
                        hour_key = conn_time.strftime('%Y-%m-%d %H:00:00')
                        hourly_data[hour_key] += 1
                except:
                    continue
        
        # Create time series data
        history = []
        for i in range(hours):
            timestamp = current_time - timedelta(hours=hours-i)
            hour_key = timestamp.strftime('%Y-%m-%d %H:00:00')
            
            history.append({
                'timestamp': timestamp.isoformat(),
                'active_connections': hourly_data.get(hour_key, 0),
                'hour': timestamp.strftime('%H:%M')
            })
        
        return jsonify({
            'connections_history': history,
            'hours': hours
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize the application
    init_default_settings()
    init_ml_model()
    
    # Start monitoring if enabled
    monitoring_enabled = db_manager.get_setting('monitoring_enabled') == 'true'
    dev_mode = db_manager.get_setting('dev_mode') == 'true'
    
    if monitoring_enabled and traffic_monitor:
        traffic_monitor.start_monitoring(dev_mode=dev_mode)
        print(f"Network monitoring started (dev_mode: {dev_mode})")
    
    print("NetGuard application starting...")
    print("Dashboard: http://localhost:5000")
    if dev_mode:
        print("Dev mode enabled - detailed traffic logging active")
        print("HTTP Proxy: Configure browser to use 127.0.0.1:8080")
    
    app.run(debug=True, host='0.0.0.0', port=5000)