#!/usr/bin/env python3
"""
Log Monitoring Module

Monitors system logs via journalctl, providing real-time log streaming
with filtering and error tracking capabilities.
"""

import subprocess
import json
from typing import Dict, List, Optional, Callable
from threading import Thread, Event
from queue import Queue, Empty
from datetime import datetime, timedelta
from collections import deque
from enum import Enum


class LogPriority(Enum):
    """Log priority levels matching systemd/journalctl."""
    EMERG = 0      # Emergency
    ALERT = 1      # Alert
    CRIT = 2       # Critical
    ERR = 3        # Error
    WARNING = 4    # Warning
    NOTICE = 5     # Notice
    INFO = 6       # Informational
    DEBUG = 7      # Debug
    
    @classmethod
    def from_string(cls, priority_str: str) -> 'LogPriority':
        """Convert string priority to enum."""
        priority_map = {
            '0': cls.EMERG,
            '1': cls.ALERT,
            '2': cls.CRIT,
            '3': cls.ERR,
            '4': cls.WARNING,
            '5': cls.NOTICE,
            '6': cls.INFO,
            '7': cls.DEBUG,
            'emerg': cls.EMERG,
            'alert': cls.ALERT,
            'crit': cls.CRIT,
            'err': cls.ERR,
            'error': cls.ERR,
            'warning': cls.WARNING,
            'warn': cls.WARNING,
            'notice': cls.NOTICE,
            'info': cls.INFO,
            'debug': cls.DEBUG,
        }
        return priority_map.get(priority_str.lower(), cls.INFO)
    
    def color_code(self) -> str:
        """Get color code for this priority level."""
        color_map = {
            LogPriority.EMERG: '#FFFFFF',      # White text
            LogPriority.ALERT: '#FFFFFF',      # White text
            LogPriority.CRIT: '#FFFFFF',       # White text
            LogPriority.ERR: '#F44336',        # Red
            LogPriority.WARNING: '#FF9800',    # Orange
            LogPriority.NOTICE: '#2196F3',     # Blue
            LogPriority.INFO: '#2196F3',       # Blue
            LogPriority.DEBUG: '#9E9E9E',      # Gray
        }
        return color_map.get(self, '#212121')
    
    def bg_color_code(self) -> Optional[str]:
        """Get background color for critical priorities."""
        if self in [LogPriority.EMERG, LogPriority.ALERT, LogPriority.CRIT]:
            return '#F44336'  # Red background
        return None


class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, raw_data: Dict):
        """Initialize from journalctl JSON output."""
        self.raw_data = raw_data
        self.timestamp = self._parse_timestamp(raw_data.get('__REALTIME_TIMESTAMP', ''))
        self.priority = self._parse_priority(raw_data.get('PRIORITY', '6'))
        self.message = raw_data.get('MESSAGE', '')
        self.source = raw_data.get('_SYSTEMD_UNIT', raw_data.get('SYSLOG_IDENTIFIER', 'system'))
        self.pid = raw_data.get('_PID', '')
        self.hostname = raw_data.get('_HOSTNAME', '')
        self.boot_id = raw_data.get('_BOOT_ID', '')
        
        # Clean up source name
        if self.source.endswith('.service'):
            self.source = self.source[:-8]
        
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse journalctl timestamp."""
        try:
            # Journal timestamps are in microseconds since epoch
            if timestamp_str:
                microsec = int(timestamp_str) / 1000000
                return datetime.fromtimestamp(microsec)
        except (ValueError, TypeError):
            pass
        return datetime.now()
    
    def _parse_priority(self, priority: str) -> LogPriority:
        """Parse priority from journalctl output."""
        return LogPriority.from_string(str(priority))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.name,
            'priority_level': self.priority.value,
            'message': self.message,
            'source': self.source,
            'pid': self.pid,
            'hostname': self.hostname,
        }
    
    def to_display_string(self) -> str:
        """Format for display in log viewer."""
        time_str = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        priority_str = self.priority.name.ljust(8)
        source_str = self.source[:20].ljust(20)
        return f"{time_str} | {priority_str} | {source_str} | {self.message}"


class LogMonitor:
    """Monitors system logs via journalctl."""
    
    def __init__(
        self,
        update_interval: float = 1.0,
        max_entries: int = 1000,
        initial_time_range: str = "1 hour ago"
    ):
        """
        Initialize the log monitor.
        
        Args:
            update_interval: How often to check for new logs (seconds)
            max_entries: Maximum number of entries to keep in memory
            initial_time_range: Initial time range to load logs from
        """
        self.update_interval = update_interval
        self.max_entries = max_entries
        self.initial_time_range = initial_time_range
        
        # Log entries storage
        self.entries = deque(maxlen=max_entries)
        self.filtered_entries = []
        
        # Threading
        self.thread = None
        self.stop_event = Event()
        self.entry_queue = Queue()
        
        # Filters
        self.priority_filter = set()  # Set of LogPriority values
        self.source_filter = set()    # Set of source names
        self.text_filter = ""         # Text search string
        self.time_range_filter = None  # datetime range
        
        # Callbacks
        self.on_new_entry: Optional[Callable[[LogEntry], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # State
        self.is_running = False
        self.is_paused = False
        self.last_timestamp = datetime.now()
        
        # Error tracking
        self.error_counts = {
            'total_errors': 0,
            'critical': 0,
            'errors': 0,
            'warnings': 0,
        }
        
    def start(self):
        """Start monitoring logs."""
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        # Load initial logs
        self._load_initial_logs()
    
    def stop(self):
        """Stop monitoring logs."""
        self.is_running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def pause(self):
        """Pause log streaming."""
        self.is_paused = True
    
    def resume(self):
        """Resume log streaming."""
        self.is_paused = False
    
    def set_priority_filter(self, priorities: List[LogPriority]):
        """Set priority filter."""
        self.priority_filter = set(priorities)
        self._apply_filters()
    
    def set_source_filter(self, sources: List[str]):
        """Set source filter."""
        self.source_filter = set(sources)
        self._apply_filters()
    
    def set_text_filter(self, text: str):
        """Set text search filter."""
        self.text_filter = text.lower()
        self._apply_filters()
    
    def set_time_range_filter(self, start: Optional[datetime], end: Optional[datetime]):
        """Set time range filter."""
        self.time_range_filter = (start, end)
        self._apply_filters()
    
    def clear_filters(self):
        """Clear all filters."""
        self.priority_filter.clear()
        self.source_filter.clear()
        self.text_filter = ""
        self.time_range_filter = None
        self._apply_filters()
    
    def _load_initial_logs(self):
        """Load initial log entries."""
        try:
            cmd = [
                'journalctl',
                '--since', self.initial_time_range,
                '--no-pager',
                '-o', 'json',
                '-n', str(self.max_entries)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            entry = LogEntry(data)
                            self.entries.append(entry)
                            self._update_error_counts(entry)
                            if entry.timestamp > self.last_timestamp:
                                self.last_timestamp = entry.timestamp
                        except json.JSONDecodeError:
                            continue
                
                self._apply_filters()
        except subprocess.TimeoutExpired:
            if self.on_error:
                self.on_error("Timeout loading initial logs")
        except FileNotFoundError:
            if self.on_error:
                self.on_error("journalctl not found. Install systemd to use log monitoring.")
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error loading logs: {str(e)}")
    
    def _monitor_loop(self):
        """Main monitoring loop running in background thread."""
        while self.is_running and not self.stop_event.is_set():
            if not self.is_paused:
                self._fetch_new_logs()
            
            self.stop_event.wait(self.update_interval)
    
    def _fetch_new_logs(self):
        """Fetch new log entries since last check."""
        try:
            # Use --since with last timestamp
            since_str = self.last_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            cmd = [
                'journalctl',
                '--since', since_str,
                '--no-pager',
                '-o', 'json',
                '-n', '100'  # Limit batch size
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                new_entries = []
                
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            entry = LogEntry(data)
                            
                            # Only process new entries
                            if entry.timestamp > self.last_timestamp:
                                self.entries.append(entry)
                                self._update_error_counts(entry)
                                new_entries.append(entry)
                                if entry.timestamp > self.last_timestamp:
                                    self.last_timestamp = entry.timestamp
                        except json.JSONDecodeError:
                            continue
                
                # Notify of new entries
                if new_entries and self.on_new_entry:
                    for entry in new_entries:
                        if self._matches_filters(entry):
                            self.on_new_entry(entry)
                
                # Update filtered view
                if new_entries:
                    self._apply_filters()
                    
        except subprocess.TimeoutExpired:
            pass  # Timeout is acceptable, just skip this update
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error fetching logs: {str(e)}")
    
    def _update_error_counts(self, entry: LogEntry):
        """Update error tracking counts."""
        if entry.priority == LogPriority.CRIT or entry.priority == LogPriority.ALERT:
            self.error_counts['critical'] += 1
            self.error_counts['total_errors'] += 1
        elif entry.priority == LogPriority.ERR:
            self.error_counts['errors'] += 1
            self.error_counts['total_errors'] += 1
        elif entry.priority == LogPriority.WARNING:
            self.error_counts['warnings'] += 1
    
    def _matches_filters(self, entry: LogEntry) -> bool:
        """Check if entry matches current filters."""
        # Priority filter
        if self.priority_filter and entry.priority not in self.priority_filter:
            return False
        
        # Source filter
        if self.source_filter and entry.source not in self.source_filter:
            return False
        
        # Text filter
        if self.text_filter:
            if self.text_filter not in entry.message.lower():
                if self.text_filter not in entry.source.lower():
                    return False
        
        # Time range filter
        if self.time_range_filter:
            start, end = self.time_range_filter
            if start and entry.timestamp < start:
                return False
            if end and entry.timestamp > end:
                return False
        
        return True
    
    def _apply_filters(self):
        """Apply filters to all entries."""
        self.filtered_entries = [
            entry for entry in self.entries
            if self._matches_filters(entry)
        ]
    
    def get_filtered_entries(self) -> List[LogEntry]:
        """Get filtered log entries."""
        return self.filtered_entries
    
    def get_all_entries(self) -> List[LogEntry]:
        """Get all log entries."""
        return list(self.entries)
    
    def get_error_summary(self) -> Dict:
        """Get error summary statistics."""
        recent_critical = sum(
            1 for e in self.entries
            if e.priority in [LogPriority.CRIT, LogPriority.ALERT]
            and (datetime.now() - e.timestamp).total_seconds() < 3600
        )
        
        recent_errors = sum(
            1 for e in self.entries
            if e.priority == LogPriority.ERR
            and (datetime.now() - e.timestamp).total_seconds() < 3600
        )
        
        return {
            **self.error_counts,
            'recent_critical_1h': recent_critical,
            'recent_errors_1h': recent_errors,
        }
    
    def get_available_sources(self) -> List[str]:
        """Get list of available log sources."""
        sources = set()
        for entry in self.entries:
            if entry.source:
                sources.add(entry.source)
        return sorted(sources)

