import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import threading
import os

class DatabaseManager:
    def __init__(self, db_path: str = "netguard.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Detection logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL NOT NULL,
                    is_gambling BOOLEAN NOT NULL,
                    headers TEXT,
                    content_snippet TEXT,
                    blocked BOOLEAN DEFAULT FALSE,
                    method TEXT,
                    status_code INTEGER,
                    response_size INTEGER
                )
            ''')
            
            # Traffic logs table (for dev mode)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_ip TEXT,
                    dest_ip TEXT,
                    source_port INTEGER,
                    dest_port INTEGER,
                    protocol TEXT,
                    url TEXT,
                    method TEXT,
                    headers TEXT,
                    request_body TEXT,
                    response_headers TEXT,
                    response_body TEXT,
                    status_code INTEGER,
                    response_size INTEGER,
                    duration_ms REAL
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL
                )
            ''')
            
            # Blocked sites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            ''')
            
            # Network connections table (real-time)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    local_ip TEXT,
                    local_port INTEGER,
                    remote_ip TEXT,
                    remote_port INTEGER,
                    status TEXT,
                    pid INTEGER,
                    process_name TEXT
                )
            ''')
            
            # Bandwidth history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bandwidth_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    bytes_sent INTEGER,
                    bytes_recv INTEGER,
                    bandwidth_mbps REAL,
                    active_connections INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def log_detection(self, url: str, confidence: float, is_gambling: bool, 
                     headers: Dict = None, content: str = None, blocked: bool = False,
                     method: str = None, status_code: int = None, response_size: int = None) -> int:
        """Log a gambling detection"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO detection_logs 
                (url, confidence, is_gambling, headers, content_snippet, blocked, method, status_code, response_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url, confidence, is_gambling, 
                json.dumps(headers) if headers else None,
                content[:1000] if content else None,
                blocked, method, status_code, response_size
            ))
            
            detection_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return detection_id
    
    def log_traffic(self, source_ip: str, dest_ip: str, source_port: int, dest_port: int,
                   protocol: str, url: str = None, method: str = None, headers: Dict = None,
                   request_body: str = None, response_headers: Dict = None, 
                   response_body: str = None, status_code: int = None, 
                   response_size: int = None, duration_ms: float = None) -> int:
        """Log network traffic (dev mode)"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO traffic_logs 
                (source_ip, dest_ip, source_port, dest_port, protocol, url, method, 
                 headers, request_body, response_headers, response_body, status_code, 
                 response_size, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_ip, dest_ip, source_port, dest_port, protocol, url, method,
                json.dumps(headers) if headers else None,
                request_body[:5000] if request_body else None,
                json.dumps(response_headers) if response_headers else None,
                response_body[:5000] if response_body else None,
                status_code, response_size, duration_ms
            ))
            
            traffic_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return traffic_id
    
    def log_connection(self, local_ip: str, local_port: int, remote_ip: str, 
                      remote_port: int, status: str, pid: int = None, 
                      process_name: str = None) -> int:
        """Log network connection"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO network_connections 
                (local_ip, local_port, remote_ip, remote_port, status, pid, process_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (local_ip, local_port, remote_ip, remote_port, status, pid, process_name))
            
            conn_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return conn_id
    
    def log_bandwidth(self, bytes_sent: int, bytes_recv: int, 
                     bandwidth_mbps: float, active_connections: int) -> int:
        """Log bandwidth usage data"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bandwidth_history 
                (bytes_sent, bytes_recv, bandwidth_mbps, active_connections)
                VALUES (?, ?, ?, ?)
            ''', (bytes_sent, bytes_recv, bandwidth_mbps, active_connections))
            
            bandwidth_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return bandwidth_id
    
    def get_bandwidth_history(self, hours: int = 24) -> List[Dict]:
        """Get bandwidth history for the specified time period"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT timestamp, bytes_sent, bytes_recv, bandwidth_mbps, active_connections
                FROM bandwidth_history 
                WHERE timestamp > ? 
                ORDER BY timestamp ASC
            ''', (since.isoformat(),))
            
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'timestamp': row[0],
                    'bytes_sent': row[1],
                    'bytes_recv': row[2],
                    'bandwidth_mbps': row[3],
                    'active_connections': row[4],
                    'hour': datetime.fromisoformat(row[0]).strftime('%H:%M') if row[0] else ''
                })
            
            conn.close()
            return history
    
    def get_detections(self, limit: int = 100, offset: int = 0, 
                      search: str = None) -> List[Dict]:
        """Get detection logs with pagination"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, url, timestamp, confidence, is_gambling, headers, 
                       content_snippet, blocked, method, status_code, response_size
                FROM detection_logs
            '''
            params = []
            
            if search:
                query += ' WHERE url LIKE ?'
                params.append(f'%{search}%')
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            detections = []
            for row in rows:
                detections.append({
                    'id': row[0],
                    'url': row[1],
                    'timestamp': datetime.fromisoformat(row[2]) if row[2] else None,
                    'confidence': row[3],
                    'is_gambling': bool(row[4]),
                    'headers': json.loads(row[5]) if row[5] else None,
                    'content_snippet': row[6],
                    'blocked': bool(row[7]),
                    'method': row[8],
                    'status_code': row[9],
                    'response_size': row[10]
                })
            
            conn.close()
            return detections
    
    def get_traffic_logs(self, limit: int = 100, offset: int = 0, 
                        hours: int = 24) -> List[Dict]:
        """Get traffic logs for dev mode"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT * FROM traffic_logs 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (since.isoformat(), limit, offset))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            traffic_logs = []
            for row in rows:
                log_dict = dict(zip(columns, row))
                # Parse JSON fields
                for field in ['headers', 'response_headers']:
                    if log_dict.get(field):
                        try:
                            log_dict[field] = json.loads(log_dict[field])
                        except:
                            pass
                traffic_logs.append(log_dict)
            
            conn.close()
            return traffic_logs
    
    def get_connections(self, limit: int = 100) -> List[Dict]:
        """Get recent network connections"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM network_connections 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            connections = []
            for row in rows:
                connections.append(dict(zip(columns, row)))
            
            conn.close()
            return connections
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total detections
            cursor.execute('SELECT COUNT(*) FROM detection_logs')
            total_detections = cursor.fetchone()[0]
            
            # Blocked sites
            cursor.execute('SELECT COUNT(*) FROM detection_logs WHERE blocked = 1')
            blocked_count = cursor.fetchone()[0]
            
            # Recent detections (last 24h)
            since = datetime.now() - timedelta(hours=24)
            cursor.execute('SELECT COUNT(*) FROM detection_logs WHERE timestamp > ?', 
                          (since.isoformat(),))
            recent_detections = cursor.fetchone()[0]
            
            # Gambling detections
            cursor.execute('SELECT COUNT(*) FROM detection_logs WHERE is_gambling = 1')
            gambling_detections = cursor.fetchone()[0]
            
            # Traffic volume (last 24h)
            cursor.execute('SELECT COUNT(*) FROM traffic_logs WHERE timestamp > ?', 
                          (since.isoformat(),))
            traffic_volume = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_detections': total_detections,
                'blocked_count': blocked_count,
                'recent_detections': recent_detections,
                'gambling_detections': gambling_detections,
                'traffic_volume': traffic_volume
            }
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            conn.close()
            return result[0] if result else None
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value) 
                VALUES (?, ?)
            ''', (key, value))
            
            conn.commit()
            conn.close()
    
    def add_blocked_site(self, url: str, reason: str = None) -> bool:
        """Add a site to the blocked list"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO blocked_sites (url, reason) 
                    VALUES (?, ?)
                ''', (url, reason))
                
                conn.commit()
                conn.close()
                return True
            except:
                return False
    
    def remove_blocked_site(self, url: str) -> bool:
        """Remove a site from the blocked list"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM blocked_sites WHERE url = ?', (url,))
                
                conn.commit()
                conn.close()
                return True
            except:
                return False
    
    def get_blocked_sites(self) -> List[Dict]:
        """Get all blocked sites"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM blocked_sites ORDER BY added_date DESC')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            blocked_sites = []
            for row in rows:
                blocked_sites.append(dict(zip(columns, row)))
            
            conn.close()
            return blocked_sites
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to prevent database bloat"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = datetime.now() - timedelta(days=days)
            
            # Clean old traffic logs (keep detection logs longer)
            cursor.execute('DELETE FROM traffic_logs WHERE timestamp < ?', 
                          (cutoff.isoformat(),))
            
            # Clean old connections
            cursor.execute('DELETE FROM network_connections WHERE timestamp < ?', 
                          (cutoff.isoformat(),))
            
            # Clean old bandwidth history (keep longer than traffic logs)
            bandwidth_cutoff = datetime.now() - timedelta(days=days*2)  # Keep bandwidth data longer
            cursor.execute('DELETE FROM bandwidth_history WHERE timestamp < ?', 
                          (bandwidth_cutoff.isoformat(),))
            
            conn.commit()
            conn.close()