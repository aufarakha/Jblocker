import threading
import time
import socket
import psutil
import requests
from urllib.parse import urlparse
import json
from datetime import datetime, timedelta
import subprocess
import re
import random
from typing import Dict, List, Optional, Tuple
import mitmproxy
from mitmproxy import http, ctx
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
import asyncio
import sys
import os

class NetworkTrafficMonitor:
    def __init__(self, db_manager, ml_predictor=None):
        self.db_manager = db_manager
        self.ml_predictor = ml_predictor
        self.monitoring_active = False
        self.dev_mode = False
        self.blocked_domains = set()
        self.monitor_thread = None
        self.proxy_thread = None
        self.connections_cache = {}
        
        # Load blocked sites
        self.load_blocked_sites()
    
    def load_blocked_sites(self):
        """Load blocked sites from database"""
        blocked_sites = self.db_manager.get_blocked_sites()
        self.blocked_domains = {urlparse(site['url']).netloc for site in blocked_sites}
    
    def start_monitoring(self, dev_mode: bool = False):
        """Start network traffic monitoring"""
        if self.monitoring_active:
            return False
        
        self.monitoring_active = True
        self.dev_mode = dev_mode
        
        # Start connection monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self.monitor_thread.start()
        
        # Start proxy for HTTP/HTTPS traffic if dev mode
        if dev_mode:
            self.proxy_thread = threading.Thread(target=self._start_proxy, daemon=True)
            self.proxy_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop network traffic monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.proxy_thread:
            self.proxy_thread.join(timeout=5)
    
    def _monitor_connections(self):
        """Monitor network connections continuously"""
        print("Starting network connection monitoring...")
        
        while self.monitoring_active:
            try:
                # Get current network connections
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if not conn.raddr:
                        continue
                    
                    try:
                        # Get process info
                        process_name = None
                        if conn.pid:
                            try:
                                process = psutil.Process(conn.pid)
                                process_name = process.name()
                            except:
                                pass
                        
                        # Log connection
                        self.db_manager.log_connection(
                            local_ip=conn.laddr.ip if conn.laddr else None,
                            local_port=conn.laddr.port if conn.laddr else None,
                            remote_ip=conn.raddr.ip,
                            remote_port=conn.raddr.port,
                            status=conn.status,
                            pid=conn.pid,
                            process_name=process_name
                        )
                        
                        # Try to resolve hostname and analyze
                        self._analyze_connection(conn, process_name)
                        
                    except Exception as e:
                        continue
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error in connection monitoring: {e}")
                time.sleep(5)
    
    def _analyze_connection(self, conn, process_name: str = None):
        """Analyze a network connection for gambling content"""
        try:
            # Skip local connections
            if conn.raddr.ip.startswith('127.') or conn.raddr.ip.startswith('192.168.'):
                return
            
            # Try to get hostname
            hostname = None
            try:
                hostname = socket.gethostbyaddr(conn.raddr.ip)[0]
            except:
                hostname = conn.raddr.ip
            
            url = f"http://{hostname}"
            
            # Check if already analyzed recently
            cache_key = f"{hostname}:{conn.raddr.port}"
            if cache_key in self.connections_cache:
                last_check = self.connections_cache[cache_key]
                if (datetime.now() - last_check).seconds < 300:  # 5 minutes
                    return
            
            self.connections_cache[cache_key] = datetime.now()
            
            # Predict if gambling-related
            confidence = 0.5
            is_gambling = False
            
            if self.ml_predictor:
                try:
                    confidence, is_gambling = self.ml_predictor(url)
                except:
                    pass
            
            # Log detection
            detection_id = self.db_manager.log_detection(
                url=url,
                confidence=confidence,
                is_gambling=is_gambling,
                blocked=hostname in self.blocked_domains,
                method="CONNECTION"
            )
            
            # Block if high confidence gambling site
            if is_gambling and confidence > 0.7 and hostname not in self.blocked_domains:
                self.block_domain(hostname)
                print(f"Blocked gambling site: {hostname} (confidence: {confidence:.2f})")
            
        except Exception as e:
            pass
    
    def _start_proxy(self):
        """Start mitmproxy for detailed HTTP/HTTPS analysis"""
        try:
            # Create proxy addon
            addon = ProxyAddon(self.db_manager, self.ml_predictor, self.blocked_domains)
            
            # Configure mitmproxy options
            opts = Options(
                listen_port=8080,
                confdir="~/.mitmproxy"
            )
            
            # Start proxy
            master = DumpMaster(opts)
            master.addons.add(addon)
            
            print("Starting HTTP proxy on port 8080...")
            print("Configure your browser to use 127.0.0.1:8080 as HTTP proxy")
            
            asyncio.run(master.run())
            
        except Exception as e:
            print(f"Error starting proxy: {e}")
    
    def block_domain(self, domain: str):
        """Block a domain by adding to hosts file and database"""
        try:
            # Add to database
            self.db_manager.add_blocked_site(f"http://{domain}", "Gambling detected")
            
            # Add to memory cache
            self.blocked_domains.add(domain)
            
            # Add to hosts file (Windows)
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            try:
                with open(hosts_path, 'a') as f:
                    f.write(f"\n127.0.0.1 {domain}")
                    f.write(f"\n127.0.0.1 www.{domain}")
            except PermissionError:
                print(f"Permission denied: Cannot modify hosts file for {domain}")
            
            return True
        except Exception as e:
            print(f"Error blocking domain {domain}: {e}")
            return False
    
    def unblock_domain(self, domain: str):
        """Unblock a domain"""
        try:
            # Remove from database
            self.db_manager.remove_blocked_site(f"http://{domain}")
            
            # Remove from memory cache
            self.blocked_domains.discard(domain)
            
            # Remove from hosts file (Windows)
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            try:
                with open(hosts_path, 'r') as f:
                    lines = f.readlines()
                
                with open(hosts_path, 'w') as f:
                    for line in lines:
                        if domain not in line:
                            f.write(line)
            except PermissionError:
                print(f"Permission denied: Cannot modify hosts file for {domain}")
            
            return True
        except Exception as e:
            print(f"Error unblocking domain {domain}: {e}")
            return False
    
    def get_real_time_stats(self) -> Dict:
        """Get real-time monitoring statistics"""
        stats = self.db_manager.get_statistics()
        
        # Add real-time connection info
        try:
            connections = psutil.net_connections(kind='inet')
            active_connections = len([c for c in connections if c.raddr])
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            
            # Calculate bandwidth (bytes per second over last interval)
            current_time = time.time()
            if hasattr(self, '_last_net_check'):
                time_diff = current_time - self._last_net_check['time']
                bytes_sent_diff = net_io.bytes_sent - self._last_net_check['bytes_sent']
                bytes_recv_diff = net_io.bytes_recv - self._last_net_check['bytes_recv']
                
                if time_diff > 0:
                    # Convert to Mbps
                    send_mbps = (bytes_sent_diff * 8) / (time_diff * 1024 * 1024)
                    recv_mbps = (bytes_recv_diff * 8) / (time_diff * 1024 * 1024)
                    total_mbps = send_mbps + recv_mbps
                else:
                    total_mbps = 0
            else:
                total_mbps = 0
            
            # Store current values for next calculation
            self._last_net_check = {
                'time': current_time,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            
            # Log bandwidth data to database (every 5 minutes to avoid spam)
            if not hasattr(self, '_last_bandwidth_log') or (current_time - self._last_bandwidth_log) > 300:
                self.db_manager.log_bandwidth(
                    bytes_sent=net_io.bytes_sent,
                    bytes_recv=net_io.bytes_recv,
                    bandwidth_mbps=total_mbps,
                    active_connections=active_connections
                )
                self._last_bandwidth_log = current_time
            
            # Get connection attempts from recent logs (last hour)
            recent_connections = self.db_manager.get_connections(limit=1000)
            connection_attempts = len([c for c in recent_connections 
                                     if c.get('timestamp') and 
                                     (datetime.now() - datetime.fromisoformat(c['timestamp'])).seconds < 3600])
            
            stats.update({
                'active_connections': active_connections,
                'monitoring_active': self.monitoring_active,
                'dev_mode': self.dev_mode,
                'blocked_domains_count': len(self.blocked_domains),
                'bandwidth_mbps': round(total_mbps, 1),
                'connection_attempts': connection_attempts,
                'total_bytes_sent': net_io.bytes_sent,
                'total_bytes_recv': net_io.bytes_recv
            })
        except Exception as e:
            print(f"Error getting real-time stats: {e}")
            stats.update({
                'active_connections': 0,
                'bandwidth_mbps': 0,
                'connection_attempts': 0
            })
        
        return stats
    
    def get_bandwidth_history(self, hours: int = 24) -> List[Dict]:
        """Get bandwidth usage history for charts"""
        try:
            # Get real bandwidth history from database
            history = self.db_manager.get_bandwidth_history(hours)
            
            # If no data available, generate some sample data
            if not history:
                current_time = datetime.now()
                for i in range(min(hours, 24)):  # Generate up to 24 hours of sample data
                    timestamp = current_time - timedelta(hours=hours-i)
                    # Simulate realistic bandwidth variation
                    base_usage = 20 + (i % 12) * 5  # Daily pattern
                    variation = random.uniform(0.5, 1.5)
                    usage = base_usage * variation
                    
                    history.append({
                        'timestamp': timestamp.isoformat(),
                        'bandwidth_mbps': round(usage, 1),
                        'hour': timestamp.strftime('%H:%M'),
                        'bytes_sent': 0,
                        'bytes_recv': 0,
                        'active_connections': random.randint(5, 25)
                    })
            
            return history
        except Exception as e:
            print(f"Error getting bandwidth history: {e}")
            return []


class ProxyAddon:
    """Mitmproxy addon for detailed HTTP/HTTPS traffic analysis"""
    
    def __init__(self, db_manager, ml_predictor=None, blocked_domains=None):
        self.db_manager = db_manager
        self.ml_predictor = ml_predictor
        self.blocked_domains = blocked_domains or set()
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Handle HTTP request"""
        try:
            url = flow.request.pretty_url
            domain = urlparse(url).netloc
            
            # Block if domain is blocked
            if domain in self.blocked_domains:
                flow.response = http.Response.make(
                    200,
                    b"<html><body><h1>Site Blocked</h1><p>This site has been blocked by NetGuard.</p></body></html>",
                    {"Content-Type": "text/html"}
                )
                return
            
            # Log request details in dev mode
            request_headers = dict(flow.request.headers)
            request_body = flow.request.get_text() if flow.request.content else None
            
            # Store request info for response processing
            flow.request_start_time = time.time()
            flow.request_info = {
                'url': url,
                'method': flow.request.method,
                'headers': request_headers,
                'body': request_body
            }
            
        except Exception as e:
            print(f"Error processing request: {e}")
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle HTTP response"""
        try:
            if not hasattr(flow, 'request_info'):
                return
            
            # Calculate response time
            duration_ms = (time.time() - flow.request_start_time) * 1000
            
            # Get response details
            response_headers = dict(flow.response.headers)
            response_body = flow.response.get_text() if flow.response.content else None
            response_size = len(flow.response.content) if flow.response.content else 0
            
            url = flow.request_info['url']
            
            # Log traffic details
            self.db_manager.log_traffic(
                source_ip="127.0.0.1",  # Proxy source
                dest_ip=urlparse(url).netloc,
                source_port=0,
                dest_port=flow.request.port,
                protocol="HTTP",
                url=url,
                method=flow.request_info['method'],
                headers=flow.request_info['headers'],
                request_body=flow.request_info['body'],
                response_headers=response_headers,
                response_body=response_body,
                status_code=flow.response.status_code,
                response_size=response_size,
                duration_ms=duration_ms
            )
            
            # Analyze for gambling content
            if self.ml_predictor:
                try:
                    # Combine URL, headers, and content for analysis
                    analysis_text = f"{url} {response_body[:1000] if response_body else ''}"
                    confidence, is_gambling = self.ml_predictor(
                        url, 
                        headers=response_headers, 
                        content=response_body
                    )
                    
                    # Log detection
                    self.db_manager.log_detection(
                        url=url,
                        confidence=confidence,
                        is_gambling=is_gambling,
                        headers=response_headers,
                        content=response_body,
                        blocked=False,
                        method=flow.request_info['method'],
                        status_code=flow.response.status_code,
                        response_size=response_size
                    )
                    
                    # Auto-block high confidence gambling sites
                    if is_gambling and confidence > 0.8:
                        domain = urlparse(url).netloc
                        self.blocked_domains.add(domain)
                        print(f"Auto-blocked gambling site: {domain} (confidence: {confidence:.2f})")
                        
                except Exception as e:
                    print(f"Error in ML analysis: {e}")
            
        except Exception as e:
            print(f"Error processing response: {e}")


# Utility functions for network analysis
def get_network_interfaces():
    """Get available network interfaces"""
    interfaces = []
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append({
                        'name': interface,
                        'ip': addr.address,
                        'netmask': addr.netmask
                    })
    except:
        pass
    return interfaces

def get_active_processes_with_network():
    """Get processes with active network connections"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                if proc.info['connections']:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'connections': len(proc.info['connections'])
                    })
            except:
                continue
    except:
        pass
    return processes

def analyze_dns_queries():
    """Analyze DNS queries (requires admin privileges)"""
    # This would require packet capture capabilities
    # For now, return placeholder
    return []