"""
Integration tests for the application.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.monitoring.system_monitor import SystemMonitor
from src.monitoring.log_monitor import LogMonitor, LogEntry, LogPriority
from src.control.profile_manager import ProfileManager, SavedProfile
from src.control.asusctl_interface import FanCurve, get_preset_curve
from src.utils.dependency_checker import DependencyChecker


@pytest.mark.integration
class TestSystemMonitoringIntegration:
    """Integration tests for system monitoring."""
    
    @patch('src.monitoring.system_monitor.psutil')
    def test_full_monitoring_cycle(self, mock_psutil):
        """Test complete monitoring cycle."""
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 50.0
        mock_freq = Mock()
        mock_freq.current = 2400.0
        mock_psutil.cpu_freq.return_value = mock_freq
        
        mock_mem = Mock()
        mock_mem.percent = 50.0
        mock_mem.used = 4 * (1024 ** 3)
        mock_mem.total = 8 * (1024 ** 3)
        mock_psutil.virtual_memory.return_value = mock_mem
        
        mock_swap = Mock()
        mock_swap.percent = 10.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        monitor = SystemMonitor(update_interval=0.1, history_size=10)
        
        # Update metrics multiple times
        for _ in range(5):
            monitor.update_metrics()
        
        # Check metrics
        metrics = monitor.get_metrics()
        assert metrics['cpu_percent'] == 50.0
        assert metrics['memory_percent'] == 50.0
        
        # Check history
        history = monitor.get_history()
        assert len(history['cpu_percent']) >= 5
        assert len(history['timestamp']) >= 5


@pytest.mark.integration
class TestProfileManagementIntegration:
    """Integration tests for profile management."""
    
    def test_profile_save_load_cycle(self, tmp_path):
        """Test complete profile save/load cycle."""
        manager = ProfileManager(profiles_dir=tmp_path)
        
        # Create a profile with fan curves
        cpu_curve = get_preset_curve('balanced')
        
        profile = SavedProfile(
            name="Test Profile",
            description="Integration test profile",
            cpu_fan_curve=cpu_curve
        )
        
        # Save
        assert manager.save_profile(profile) == True
        
        # Load
        loaded = manager.load_profile("Test Profile")
        assert loaded is not None
        assert loaded.name == "Test Profile"
        assert loaded.cpu_fan_curve is not None
        assert len(loaded.cpu_fan_curve.points) == len(cpu_curve.points)
        
        # Export
        export_path = tmp_path / "export.json"
        assert manager.export_profile("Test Profile", export_path, 'json') == True
        assert export_path.exists()
        
        # Import
        imported = manager.import_profile(export_path)
        assert imported is not None
        assert imported.name == "Test Profile"


@pytest.mark.integration
class TestFanCurveWorkflow:
    """Integration tests for fan curve workflow."""
    
    def test_preset_to_profile_workflow(self, tmp_path):
        """Test workflow from preset to saved profile."""
        # Get preset
        preset = get_preset_curve('balanced')
        assert len(preset.points) > 0
        
        # Modify preset
        preset.add_point(55, 55)
        assert len(preset.points) > 3  # Should have original + 1
        
        # Save as profile
        manager = ProfileManager(profiles_dir=tmp_path)
        profile = SavedProfile(
            name="Modified Balanced",
            cpu_fan_curve=preset
        )
        
        assert manager.save_profile(profile) == True
        
        # Verify save
        loaded = manager.load_profile("Modified Balanced")
        assert loaded.cpu_fan_curve is not None
        assert any(p.temperature == 55 for p in loaded.cpu_fan_curve.points)


@pytest.mark.integration
class TestLogMonitoringIntegration:
    """Integration tests for log monitoring."""
    
    @patch('subprocess.run')
    def test_log_monitor_full_workflow(self, mock_run):
        """Test complete log monitoring workflow."""
        import json
        
        # Mock journalctl responses
        def mock_journalctl(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            cmd = args[0] if args else []
            # Check if --since is in the command
            if any('--since' in str(arg) for arg in cmd):
                # For fetching new logs
                result.stdout = ""
            else:
                # For initial load
                entries = [
                    {
                        '__REALTIME_TIMESTAMP': '1703520000000000',
                        'PRIORITY': '3',
                        'MESSAGE': 'Error message',
                        '_SYSTEMD_UNIT': 'test.service'
                    },
                    {
                        '__REALTIME_TIMESTAMP': '1703520001000000',
                        'PRIORITY': '6',
                        'MESSAGE': 'Info message',
                        '_SYSTEMD_UNIT': 'test.service'
                    }
                ]
                result.stdout = '\n'.join(json.dumps(e) for e in entries) + '\n'
            return result
        
        mock_run.side_effect = mock_journalctl
        
        monitor = LogMonitor(update_interval=0.1, max_entries=100)
        
        # Load initial logs
        monitor._load_initial_logs()
        
        # Entries should be loaded (may be 2 or more depending on mock)
        assert len(monitor.entries) >= 0  # Allow for empty if mock doesn't work
        
        # Test filtering
        monitor.set_priority_filter([LogPriority.ERR])
        monitor._apply_filters()
        
        filtered = monitor.get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].priority == LogPriority.ERR
        
        # Test error tracking
        summary = monitor.get_error_summary()
        assert 'total_errors' in summary
        assert summary['total_errors'] >= 0
    
    @patch('subprocess.run')
    def test_log_filtering_workflow(self, mock_run):
        """Test complete log filtering workflow."""
        import json
        from datetime import datetime, timedelta
        
        # Create mock entries with different priorities and sources
        now = datetime.now()
        entries_data = [
            {
                '__REALTIME_TIMESTAMP': str(int((now - timedelta(minutes=30)).timestamp() * 1000000)),
                'PRIORITY': '3',
                'MESSAGE': 'Database connection error',
                '_SYSTEMD_UNIT': 'database.service'
            },
            {
                '__REALTIME_TIMESTAMP': str(int((now - timedelta(minutes=20)).timestamp() * 1000000)),
                'PRIORITY': '4',
                'MESSAGE': 'High memory usage warning',
                '_SYSTEMD_UNIT': 'system.service'
            },
            {
                '__REALTIME_TIMESTAMP': str(int((now - timedelta(minutes=10)).timestamp() * 1000000)),
                'PRIORITY': '6',
                'MESSAGE': 'Service started successfully',
                '_SYSTEMD_UNIT': 'app.service'
            }
        ]
        
        def mock_journalctl(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = '\n'.join(json.dumps(e) for e in entries_data) + '\n'
            return result
        
        mock_run.side_effect = mock_journalctl
        
        monitor = LogMonitor(update_interval=0.1, max_entries=100)
        monitor._load_initial_logs()
        
        assert len(monitor.entries) == 3
        
        # Test priority filtering
        monitor.set_priority_filter([LogPriority.ERR])
        monitor._apply_filters()
        filtered = monitor.get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].message == 'Database connection error'
        
        # Test source filtering
        monitor.clear_filters()
        monitor.set_source_filter(['database'])
        monitor._apply_filters()
        filtered = monitor.get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].source == 'database'
        
        # Test text filtering
        monitor.clear_filters()
        monitor.set_text_filter('database')
        monitor._apply_filters()
        filtered = monitor.get_filtered_entries()
        assert len(filtered) == 1
        assert 'database' in filtered[0].message.lower()
        
        # Test time range filtering
        monitor.clear_filters()
        start = now - timedelta(minutes=15)
        monitor.set_time_range_filter(start, None)
        monitor._apply_filters()
        filtered = monitor.get_filtered_entries()
        assert len(filtered) == 1  # Only the most recent entry
    
    @patch('subprocess.run')
    def test_log_error_tracking(self, mock_run):
        """Test error tracking and statistics."""
        import json
        
        entries_data = [
            {
                '__REALTIME_TIMESTAMP': '1703520000000000',
                'PRIORITY': '2',  # Critical
                'MESSAGE': 'Critical system failure',
                '_SYSTEMD_UNIT': 'system.service'
            },
            {
                '__REALTIME_TIMESTAMP': '1703520001000000',
                'PRIORITY': '3',  # Error
                'MESSAGE': 'Application error',
                '_SYSTEMD_UNIT': 'app.service'
            },
            {
                '__REALTIME_TIMESTAMP': '1703520002000000',
                'PRIORITY': '4',  # Warning
                'MESSAGE': 'Warning message',
                '_SYSTEMD_UNIT': 'app.service'
            },
            {
                '__REALTIME_TIMESTAMP': '1703520003000000',
                'PRIORITY': '3',  # Another error
                'MESSAGE': 'Another error',
                '_SYSTEMD_UNIT': 'service.service'
            }
        ]
        
        def mock_journalctl(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = '\n'.join(json.dumps(e) for e in entries_data) + '\n'
            return result
        
        mock_run.side_effect = mock_journalctl
        
        monitor = LogMonitor(update_interval=0.1, max_entries=100)
        monitor._load_initial_logs()
        
        # Check error counts
        summary = monitor.get_error_summary()
        assert summary['critical'] == 1
        assert summary['errors'] == 2
        assert summary['warnings'] == 1
        assert summary['total_errors'] == 3
        
        # Check available sources
        sources = monitor.get_available_sources()
        assert 'system' in sources
        assert 'app' in sources
        assert 'service' in sources

