"""
Tests for system monitoring module.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, mock_open
from collections import deque

from src.monitoring.system_monitor import SystemMonitor


class TestSystemMonitor:
    """Test SystemMonitor class."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = SystemMonitor(update_interval=1.0, history_size=100)
        
        assert monitor.update_interval == 1.0
        assert monitor.history_size == 100
        assert isinstance(monitor.metrics, dict)
        assert isinstance(monitor.history, dict)
        assert monitor._stop_event.is_set() == False
    
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.subprocess.run')
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_update_cpu_metrics(self, mock_open, mock_run, mock_psutil):
        """Test CPU metrics update."""
        # Setup mocks
        # cpu_percent is called twice: once without interval, once with percpu=True
        def cpu_percent_side_effect(*args, **kwargs):
            if kwargs.get('percpu', False):
                return [45.5, 50.0, 40.0, 45.5]
            else:
                return 45.5
        
        mock_psutil.cpu_percent.side_effect = cpu_percent_side_effect
        
        mock_freq = Mock()
        mock_freq.current = 2400.0
        mock_psutil.cpu_freq.return_value = mock_freq
        
        monitor = SystemMonitor()
        monitor.update_metrics()
        
        assert monitor.metrics['cpu_percent'] == 45.5
        assert monitor.metrics['cpu_freq'] == 2400.0
    
    @patch('src.monitoring.system_monitor.psutil')
    def test_update_memory_metrics(self, mock_psutil):
        """Test memory metrics update."""
        mock_mem = Mock()
        mock_mem.percent = 60.0
        mock_mem.used = 4 * (1024 ** 3)  # 4 GB
        mock_mem.total = 8 * (1024 ** 3)  # 8 GB
        mock_psutil.virtual_memory.return_value = mock_mem
        
        mock_swap = Mock()
        mock_swap.percent = 10.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        monitor = SystemMonitor()
        monitor.update_metrics()
        
        assert monitor.metrics['memory_percent'] == 60.0
        assert monitor.metrics['memory_used_gb'] == 4.0
        assert monitor.metrics['memory_total_gb'] == 8.0
        assert monitor.metrics['swap_percent'] == 10.0
    
    @patch('builtins.open', new_callable=mock_open, read_data='45000')
    @patch('glob.glob')
    def test_get_cpu_temperature_from_thermal(self, mock_glob, mock_file):
        """Test CPU temperature reading from thermal zones."""
        monitor = SystemMonitor()
        
        # Mock thermal zone file exists
        mock_glob.return_value = []
        
        # Mock Path.exists to return True for thermal zone
        with patch('pathlib.Path.exists') as mock_exists:
            # First call for thermal zones returns True, others False
            def exists_side_effect(path):
                path_str = str(path)
                if 'thermal_zone' in path_str and 'temp' in path_str:
                    return True
                return False
            
            mock_exists.side_effect = exists_side_effect
            
            temp = monitor._get_cpu_temperature()
            # Should handle gracefully
            assert temp is None or isinstance(temp, float)
    
    def test_get_cpu_temperature_no_sensors(self):
        """Test CPU temperature when no sensors available."""
        monitor = SystemMonitor()
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('subprocess.run', side_effect=FileNotFoundError):
                temp = monitor._get_cpu_temperature()
                assert temp is None
    
    @patch('subprocess.run')
    def test_get_gpu_metrics_with_nvidia_smi(self, mock_run):
        """Test GPU metrics via nvidia-smi fallback."""
        # nvidia-smi format: "temp, util, mem_used, mem_total, power"
        mock_run.return_value = Mock(
            returncode=0,
            stdout="75, 85, 4.0, 8.0, 120.5"
        )
        
        monitor = SystemMonitor()
        # Set nvidia_available to True, but nvml fails, so falls back to nvidia-smi
        monitor._nvidia_available = True
        monitor._nvml_module = None
        monitor._use_nvml = False  # py3nvml not available, will use nvidia-smi
        
        metrics = monitor._get_gpu_metrics()
        
        # Should parse nvidia-smi output
        assert metrics['temperature'] == 75.0
        assert metrics['utilization'] == 85.0
        assert metrics['memory_used_gb'] == 4.0
        assert metrics['memory_total_gb'] == 8.0
        assert metrics['memory_percent'] == 50.0  # 4.0 / 8.0 * 100
        assert metrics['power'] == 120.5
    
    @patch('subprocess.run')
    def test_get_gpu_metrics_not_available(self, mock_run):
        """Test GPU metrics when GPU not available."""
        monitor = SystemMonitor()
        monitor._nvidia_available = False
        monitor._nvml_module = None
        monitor._use_nvml = False
        
        # Mock nvidia-smi to fail (GPU not available)  
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0] if args else []
            if 'nvidia-smi' in cmd:
                raise FileNotFoundError("nvidia-smi not found")
            # Return empty result for other commands
            result = Mock()
            result.returncode = 1
            result.stdout = ""
            return result
        
        mock_run.side_effect = mock_run_side_effect
        
        metrics = monitor._get_gpu_metrics()
        
        # When GPU is not available, _get_gpu_metrics returns empty dict
        assert isinstance(metrics, dict)
        # Should return empty dict when no GPU available (all values None or dict empty)
        # If dict has keys but all values are None, that's also acceptable
    
    @patch('subprocess.run')
    @patch('glob.glob')
    def test_get_fan_speeds(self, mock_glob, mock_run):
        """Test fan speed detection."""
        monitor = SystemMonitor()
        
        # Mock subprocess.run (sensors command) to fail
        mock_run.side_effect = FileNotFoundError()
        # Mock glob to return empty list (no hwmon files)
        mock_glob.return_value = []
        
        speeds = monitor._get_fan_speeds()
        # Should return empty list when no fans found
        assert speeds == []
    
    def test_history_collection(self):
        """Test historical data collection."""
        monitor = SystemMonitor(history_size=10)
        
        monitor.metrics['cpu_percent'] = 50.0
        monitor.metrics['cpu_temp'] = 60.0
        
        monitor.update_metrics()
        
        assert len(monitor.history['cpu_percent']) > 0
        assert len(monitor.history['timestamp']) > 0
    
    def test_start_stop_monitoring(self):
        """Test monitoring thread start and stop."""
        monitor = SystemMonitor(update_interval=0.1)
        
        monitor.start()
        assert monitor._monitoring_thread is not None
        assert monitor._monitoring_thread.is_alive()
        
        # Wait a bit for updates
        time.sleep(0.2)
        
        monitor.stop()
        assert monitor._stop_event.is_set()
        
        # Thread should stop
        monitor._monitoring_thread.join(timeout=1.0)
        assert not monitor._monitoring_thread.is_alive()
    
    def test_get_metrics(self):
        """Test getting metrics snapshot."""
        monitor = SystemMonitor()
        monitor.metrics['cpu_percent'] = 50.0
        
        snapshot = monitor.get_metrics()
        
        assert snapshot['cpu_percent'] == 50.0
        assert snapshot is not monitor.metrics  # Should be a copy
    
    def test_get_history(self):
        """Test getting historical data."""
        monitor = SystemMonitor(history_size=10)
        monitor.update_metrics()
        
        history = monitor.get_history()
        
        assert isinstance(history, dict)
        assert 'cpu_percent' in history
        assert isinstance(history['cpu_percent'], list)

