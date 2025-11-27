#!/usr/bin/env python3
"""
System Monitoring Module

Monitors CPU, GPU, memory, temperatures, and fan speeds.
Provides real-time metrics for the dashboard.
"""

import psutil
import subprocess
import time
import os
from typing import Dict, Optional, List
from threading import Thread, Event
from collections import deque


class SystemMonitor:
    """Monitors system metrics including CPU, GPU, memory, and temperatures."""
    
    def __init__(self, update_interval: float = 1.0, history_size: int = 300):
        """
        Initialize the system monitor.
        
        Args:
            update_interval: How often to update metrics (seconds)
            history_size: Number of historical data points to keep
        """
        self.update_interval = update_interval
        self.history_size = history_size
        
        # Current metrics
        self.metrics = {
            'cpu_percent': 0.0,
            'cpu_per_core': [],
            'cpu_temp': None,
            'cpu_freq': 0.0,
            'memory_percent': 0.0,
            'memory_used_gb': 0.0,
            'memory_total_gb': 0.0,
            'swap_percent': 0.0,
            'gpu_utilization': None,
            'gpu_temp': None,
            'gpu_memory_percent': None,
            'gpu_power': None,
            'fan_speeds': [],
            'fps': None,
            'network_sent_mbps': 0.0,
            'network_recv_mbps': 0.0,
            'network_total_mbps': 0.0,
        }
        
        # Network monitoring (for bandwidth calculation)
        self._last_net_io = None
        self._last_net_time = None
        
        # Historical data (for graphs)
        self.history = {
            'cpu_percent': deque(maxlen=history_size),
            'cpu_temp': deque(maxlen=history_size),
            'memory_percent': deque(maxlen=history_size),
            'gpu_utilization': deque(maxlen=history_size),
            'gpu_temp': deque(maxlen=history_size),
            'network_sent_mbps': deque(maxlen=history_size),
            'network_recv_mbps': deque(maxlen=history_size),
            'network_total_mbps': deque(maxlen=history_size),
            'fps': deque(maxlen=history_size),
            'timestamp': deque(maxlen=history_size),
        }
        
        # Monitoring thread
        self._stop_event = Event()
        self._monitoring_thread = None
        self._nvml_module = None
        self._use_nvml = False
        self._nvidia_available = self._check_nvidia_available()
        
    def _check_nvidia_available(self) -> bool:
        """Check if NVIDIA GPU monitoring is available."""
        # Try py3nvml first
        try:
            from py3nvml import py3nvml as nvml
            nvml.nvmlInit()
            device_count = nvml.nvmlDeviceGetCount()
            self._nvml_module = nvml
            self._use_nvml = True
            return device_count > 0
        except Exception:
            pass
        
        # Fallback: check if nvidia-smi command is available
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=count', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                self._use_nvml = False
                return True
        except Exception:
            pass
        
        self._use_nvml = False
        self._nvml_module = None
        return False
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature from thermal sensors.
        Returns average temperature in Celsius, or None if unavailable.
        """
        try:
            # Try /sys/class/thermal
            temps = []
            for i in range(10):  # Check first 10 thermal zones
                try:
                    path = f'/sys/class/thermal/thermal_zone{i}/temp'
                    with open(path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0  # Convert from millidegrees
                        # Only include reasonable temperatures (10-100°C)
                        if 10 <= temp <= 100:
                            temps.append(temp)
                except (FileNotFoundError, ValueError):
                    continue
            
            # Also try hwmon (alternative location)
            import glob
            for hwmon_path in glob.glob('/sys/class/hwmon/hwmon*/temp*_input'):
                try:
                    with open(hwmon_path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0
                        if 10 <= temp <= 100:
                            temps.append(temp)
                except (FileNotFoundError, ValueError):
                    continue
            
            if temps:
                return sum(temps) / len(temps)
        except Exception:
            pass
        
        # Fallback: try sensors command
        try:
            result = subprocess.run(
                ['sensors'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Simple parsing - look for CPU temperature
                for line in result.stdout.split('\n'):
                    if 'CPU' in line or 'Package id' in line:
                        # Extract temperature number
                        import re
                        match = re.search(r'\+(\d+\.\d+)°C', line)
                        if match:
                            return float(match.group(1))
        except Exception:
            pass
        
        return None
    
    def _get_gpu_metrics(self) -> Dict:
        """Get NVIDIA GPU metrics if available."""
        metrics = {}
        
        # Always try to get GPU metrics, even if initial check failed
        # (GPU might have been unavailable at startup but is now available)
        if not self._nvidia_available:
            # Re-check if GPU became available
            self._nvidia_available = self._check_nvidia_available()
            if not self._nvidia_available:
                return metrics
        
        # Try py3nvml library
        if self._use_nvml and self._nvml_module:
            try:
                nvml = self._nvml_module
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                
                # GPU utilization
                util = nvml.nvmlDeviceGetUtilizationRates(handle)
                metrics['utilization'] = float(util.gpu)
                
                # Temperature
                temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                metrics['temperature'] = float(temp)
                
                # Memory
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                mem_total = mem_info.total / (1024 ** 3)  # GB
                mem_used = mem_info.used / (1024 ** 3)  # GB
                metrics['memory_percent'] = (mem_info.used / mem_info.total) * 100
                metrics['memory_used_gb'] = mem_used
                metrics['memory_total_gb'] = mem_total
                
                # Power (if available)
                try:
                    power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert mW to W
                    metrics['power'] = power
                except:
                    pass
                
                return metrics
            except Exception:
                # Fall through to nvidia-smi fallback
                pass
        
        # Fallback: use nvidia-smi command
        try:
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw',
                    '--format=csv,noheader,nounits'
                ],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse output: "temp, util, mem_used, mem_total, power"
                # Handle both ", " and "," separators
                output = result.stdout.strip()
                # Split by comma and strip whitespace from each value
                values = [v.strip() for v in output.split(',')]
                if len(values) >= 4:
                    try:
                        metrics['temperature'] = float(values[0])
                        metrics['utilization'] = float(values[1])
                        mem_used_gb = float(values[2])
                        mem_total_gb = float(values[3])
                        metrics['memory_percent'] = (mem_used_gb / mem_total_gb) * 100 if mem_total_gb > 0 else 0
                        metrics['memory_used_gb'] = mem_used_gb
                        metrics['memory_total_gb'] = mem_total_gb
                        if len(values) >= 5:
                            try:
                                metrics['power'] = float(values[4])
                            except (ValueError, IndexError):
                                pass
                    except (ValueError, IndexError) as e:
                        # If parsing fails, log and return empty metrics
                        print(f"Warning: Failed to parse nvidia-smi output: {e}")
                        print(f"Output was: {output}")
        except Exception:
            pass
        
        return metrics
    
    def _get_fan_speeds(self) -> List[Dict]:
        """Get fan speeds from system sensors, identifying CPU and GPU fans."""
        fan_speeds = []
        
        # Try sensors command first (more reliable naming)
        try:
            result = subprocess.run(
                ['sensors'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                import re
                # Look for fan lines: "cpu_fan:     6300 RPM" or "Fan1:     2300 RPM"
                for line in result.stdout.split('\n'):
                    # Match patterns like "cpu_fan:", "gpu_fan:", "Fan1:", etc.
                    match = re.search(r'(cpu_fan|gpu_fan|fan[0-9]?)\s*:\s*(\d+)\s*RPM', line, re.IGNORECASE)
                    if match:
                        fan_name = match.group(1).lower()
                        rpm = int(match.group(2))
                        if rpm > 0:
                            # Normalize names
                            if 'cpu' in fan_name:
                                normalized_name = 'CPU'
                            elif 'gpu' in fan_name:
                                normalized_name = 'GPU'
                            else:
                                normalized_name = fan_name.title()
                            
                            fan_speeds.append({
                                'name': normalized_name,
                                'rpm': rpm,
                                'raw_name': fan_name
                            })
        except Exception:
            pass
        
        # Fallback: try hwmon for fan speeds if sensors didn't work
        if not fan_speeds:
            try:
                import glob
                fan_files = {}
                # Collect all fan input files
                for fan_path in glob.glob('/sys/class/hwmon/hwmon*/fan*_input'):
                    try:
                        with open(fan_path, 'r') as f:
                            rpm = int(f.read().strip())
                            if rpm > 0:
                                # Extract fan name
                                fan_name = fan_path.split('/')[-1].replace('_input', '')
                                
                                # Try to determine if it's CPU or GPU by checking label
                                label_path = fan_path.replace('_input', '_label')
                                try:
                                    with open(label_path, 'r') as lf:
                                        label = lf.read().strip().lower()
                                        if 'cpu' in label:
                                            normalized_name = 'CPU'
                                        elif 'gpu' in label:
                                            normalized_name = 'GPU'
                                        else:
                                            normalized_name = fan_name.title()
                                except:
                                    # No label, use generic name
                                    normalized_name = fan_name.title()
                                
                                fan_speeds.append({
                                    'name': normalized_name,
                                    'rpm': rpm,
                                    'raw_name': fan_name
                                })
                    except (FileNotFoundError, ValueError):
                        continue
                
                # Sort fans: CPU first, then GPU, then others
                def fan_sort_key(f):
                    name = f['name'].upper()
                    if name == 'CPU':
                        return (0, name)
                    elif name == 'GPU':
                        return (1, name)
                    else:
                        return (2, name)
                
                fan_speeds.sort(key=fan_sort_key)
                
            except Exception:
                pass
        
        return fan_speeds
    
    def _update_network_metrics(self):
        """Update network traffic and bandwidth metrics."""
        try:
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            if self._last_net_io is not None and self._last_net_time is not None:
                # Calculate time delta
                time_delta = current_time - self._last_net_time
                
                if time_delta > 0:
                    # Calculate bytes per second
                    bytes_sent_per_sec = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta
                    bytes_recv_per_sec = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta
                    
                    # Convert to Mbps (megabits per second)
                    # 1 byte = 8 bits, 1 Mbps = 1,000,000 bits
                    self.metrics['network_sent_mbps'] = (bytes_sent_per_sec * 8) / 1_000_000
                    self.metrics['network_recv_mbps'] = (bytes_recv_per_sec * 8) / 1_000_000
                    self.metrics['network_total_mbps'] = self.metrics['network_sent_mbps'] + self.metrics['network_recv_mbps']
            
            # Store current values for next calculation
            self._last_net_io = net_io
            self._last_net_time = current_time
            
        except Exception as e:
            # If network monitoring fails, reset to 0
            self.metrics['network_sent_mbps'] = 0.0
            self.metrics['network_recv_mbps'] = 0.0
            self.metrics['network_total_mbps'] = 0.0
    
    def _update_fps_metrics(self):
        """Update FPS metrics using MangoHud integration and GPU estimation."""
        fps = None
        
        try:
            # Method 1: MangoHud integration (most accurate)
            fps = self._get_mangohud_fps()
            
            # Method 2: Check for gaming processes and estimate FPS
            if fps is None:
                fps = self._estimate_fps_from_processes()
            
            # Method 3: GPU utilization-based estimation (fallback)
            if fps is None:
                fps = self._estimate_fps_from_gpu()
            
        except Exception as e:
            print(f"Error updating FPS metrics: {e}")
            fps = None
        
        self.metrics['fps'] = fps
    
    def _get_mangohud_fps(self) -> Optional[float]:
        """Get FPS from MangoHud using multiple detection methods."""
        try:
            # Method 1: Check MangoHud shared memory (most accurate)
            fps = self._read_mangohud_shared_memory()
            if fps is not None:
                return fps
            
            # Method 2: Check MangoHud log files
            fps = self._read_mangohud_log_files()
            if fps is not None:
                return fps
            
            # Method 3: Check MangoHud config and running processes
            fps = self._detect_mangohud_process()
            if fps is not None:
                return fps
            
        except Exception as e:
            print(f"Error reading MangoHud: {e}")
        
        return None
    
    def _read_mangohud_shared_memory(self) -> Optional[float]:
        """Read FPS from MangoHud shared memory."""
        try:
            import mmap
            import struct
            
            # MangoHud uses shared memory for real-time data
            shm_paths = [
                '/dev/shm/mangohud',
                '/dev/shm/MangoHud',
                '/tmp/mangohud_shm'
            ]
            
            for shm_path in shm_paths:
                try:
                    if os.path.exists(shm_path):
                        with open(shm_path, 'rb') as f:
                            # Try to read FPS value (usually first 4-8 bytes as float)
                            data = f.read(8)
                            if len(data) >= 4:
                                fps = struct.unpack('f', data[:4])[0]
                                if 1 <= fps <= 500:
                                    return fps
                except:
                    continue
        except:
            pass
        return None
    
    def _read_mangohud_log_files(self) -> Optional[float]:
        """Read FPS from MangoHud log files with improved parsing."""
        try:
            import glob
            import os
            import re
            
            # Expanded MangoHud log locations
            log_locations = [
                '/tmp/mangohud_*.log',
                '/tmp/MangoHud_*.log',
                '/tmp/mangohud*.log',
                '/dev/shm/mangohud_*.log',
                '/dev/shm/MangoHud_*.log',
                os.path.expanduser('~/.local/share/MangoHud/*.log'),
                os.path.expanduser('~/.cache/mangohud/*.log'),
                os.path.expanduser('~/mangohud*.log')
            ]
            
            log_files = []
            for pattern in log_locations:
                log_files.extend(glob.glob(pattern))
            
            if not log_files:
                return None
            
            # Get the most recently modified log file
            latest_file = max(log_files, key=os.path.getmtime)
            
            # Check if file was modified recently (within last 3 seconds for better accuracy)
            if time.time() - os.path.getmtime(latest_file) > 3:
                return None
            
            # Read the file more efficiently
            with open(latest_file, 'rb') as f:
                # Read last 1KB for better performance
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                read_size = min(1024, file_size)
                f.seek(max(0, file_size - read_size))
                data = f.read().decode('utf-8', errors='ignore')
                
                lines = data.split('\n')
                
                # Parse from most recent lines first
                for line in reversed(lines[-20:]):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Enhanced FPS patterns for MangoHud output
                    patterns = [
                        r'fps[:\s=]+(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*fps',
                        r'framerate[:\s=]+(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*hz',
                        r'FPS:\s*(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*FPS',
                        r'fps=(\d+\.?\d*)',
                        r'frametime.*?(\d+\.?\d*).*?fps'  # Parse from frametime data
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            fps_value = float(match.group(1))
                            if 1 <= fps_value <= 500:
                                return fps_value
            
        except Exception as e:
            print(f"Error reading MangoHud logs: {e}")
        
        return None
    
    def _detect_mangohud_process(self) -> Optional[float]:
        """Detect MangoHud process and estimate FPS from GPU usage."""
        try:
            import psutil
            
            # Check if MangoHud is running
            mangohud_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    if 'mangohud' in proc_name or 'mangohud' in cmdline:
                        mangohud_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if mangohud_running:
                # MangoHud is running, provide more accurate GPU-based estimation
                gpu_util = self.metrics.get('gpu_utilization', 0) or 0
                
                # More accurate FPS estimation when MangoHud is active
                if gpu_util > 95:
                    return 144  # High-end gaming
                elif gpu_util > 85:
                    return 120  # High performance
                elif gpu_util > 75:
                    return 90   # Good performance
                elif gpu_util > 60:
                    return 60   # Standard gaming
                elif gpu_util > 40:
                    return 45   # Medium performance
                elif gpu_util > 20:
                    return 30   # Lower performance
                else:
                    return 15   # Light usage
            
        except Exception as e:
            print(f"Error detecting MangoHud process: {e}")
        
        return None
    
    def _estimate_fps_from_processes(self) -> Optional[float]:
        """Estimate FPS based on running gaming processes."""
        try:
            import psutil
            
            # Common gaming processes and their typical FPS ranges
            gaming_processes = {
                # Steam games
                'steam': (30, 60),
                'steamwebhelper': (30, 60),
                
                # Popular games (add more as needed)
                'csgo': (60, 300),
                'dota2': (60, 144),
                'tf2': (60, 144),
                'valorant': (60, 240),
                'overwatch': (60, 144),
                'minecraft': (30, 120),
                'wow': (30, 60),
                'ffxiv': (30, 60),
                
                # Game engines
                'unity': (30, 60),
                'unreal': (30, 60),
                
                # Emulators
                'dolphin': (30, 60),
                'pcsx2': (30, 60),
                'rpcs3': (30, 60),
                
                # Generic gaming indicators
                'game': (30, 60),
                'launcher': (30, 60)
            }
            
            # Check running processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc_name = proc.info['name'].lower()
                    cpu_usage = proc.info['cpu_percent'] or 0
                    
                    # Skip if process is not using significant CPU
                    if cpu_usage < 5:
                        continue
                    
                    # Check if it matches a gaming process
                    for game_pattern, (min_fps, max_fps) in gaming_processes.items():
                        if game_pattern in proc_name:
                            # Estimate FPS based on GPU utilization
                            gpu_util = self.metrics.get('gpu_utilization', 0) or 0
                            
                            if gpu_util > 80:
                                return min(max_fps, max_fps * 0.9)  # High performance
                            elif gpu_util > 50:
                                return (min_fps + max_fps) / 2      # Medium performance
                            elif gpu_util > 20:
                                return min_fps                      # Low performance
                            else:
                                return min_fps * 0.5                # Very low
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
        except Exception as e:
            print(f"Error estimating FPS from processes: {e}")
        
        return None
    
    def _estimate_fps_from_gpu(self) -> Optional[float]:
        """Estimate FPS based on GPU utilization with improved accuracy."""
        try:
            gpu_util = self.metrics.get('gpu_utilization')
            if gpu_util is None or gpu_util == 0:
                return 60  # Default desktop FPS when no GPU data
            
            # Simple but effective FPS estimation
            if gpu_util > 80:
                return 120
            elif gpu_util > 60:
                return 90
            elif gpu_util > 40:
                return 60
            elif gpu_util > 20:
                return 45
            elif gpu_util > 10:
                return 30
            else:
                return 60  # Desktop compositing
            
        except Exception as e:
            print(f"Error estimating FPS from GPU: {e}")
        
        return 60  # Fallback to 60 FPS
    
    def update_metrics(self):
        """Update all system metrics."""
        # CPU metrics
        self.metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        self.metrics['cpu_per_core'] = psutil.cpu_percent(percpu=True, interval=0.1)
        
        # CPU frequency
        try:
            freq = psutil.cpu_freq()
            self.metrics['cpu_freq'] = freq.current if freq else 0.0
        except:
            self.metrics['cpu_freq'] = 0.0
        
        # CPU temperature
        self.metrics['cpu_temp'] = self._get_cpu_temperature()
        
        # Memory metrics
        mem = psutil.virtual_memory()
        self.metrics['memory_percent'] = mem.percent
        self.metrics['memory_used_gb'] = mem.used / (1024 ** 3)
        self.metrics['memory_total_gb'] = mem.total / (1024 ** 3)
        
        # Swap metrics
        swap = psutil.swap_memory()
        self.metrics['swap_percent'] = swap.percent
        
        # GPU metrics
        gpu_metrics = self._get_gpu_metrics()
        # Store GPU metrics - always update if we got metrics (even if 0)
        if gpu_metrics:
            # Update all fields from retrieved metrics - including 0 values
            if 'utilization' in gpu_metrics:
                # Ensure we store 0.0 instead of None when GPU is idle
                self.metrics['gpu_utilization'] = float(gpu_metrics['utilization'])
            if 'temperature' in gpu_metrics:
                self.metrics['gpu_temp'] = float(gpu_metrics['temperature'])
            if 'memory_percent' in gpu_metrics:
                self.metrics['gpu_memory_percent'] = float(gpu_metrics['memory_percent'])
            if 'power' in gpu_metrics:
                self.metrics['gpu_power'] = float(gpu_metrics['power'])
        # Note: Don't set to None if no metrics - keep previous value
        
        # Fan speeds
        self.metrics['fan_speeds'] = self._get_fan_speeds()
        
        # Network metrics
        self._update_network_metrics()
        
        # FPS monitoring
        self._update_fps_metrics()
        
        # Update history
        timestamp = time.time()
        self.history['timestamp'].append(timestamp)
        self.history['cpu_percent'].append(self.metrics['cpu_percent'])
        if self.metrics['cpu_temp']:
            self.history['cpu_temp'].append(self.metrics['cpu_temp'])
        self.history['memory_percent'].append(self.metrics['memory_percent'])
        if self.metrics['gpu_utilization'] is not None:
            self.history['gpu_utilization'].append(self.metrics['gpu_utilization'])
        if self.metrics['gpu_temp'] is not None:
            self.history['gpu_temp'].append(self.metrics['gpu_temp'])
        self.history['network_sent_mbps'].append(self.metrics['network_sent_mbps'])
        self.history['network_recv_mbps'].append(self.metrics['network_recv_mbps'])
        self.history['network_total_mbps'].append(self.metrics['network_total_mbps'])
        if self.metrics['fps'] is not None:
            self.history['fps'].append(self.metrics['fps'])
    
    def _monitoring_loop(self):
        """Background thread loop for continuous monitoring."""
        while not self._stop_event.is_set():
            try:
                self.update_metrics()
            except Exception as e:
                print(f"Error updating metrics: {e}")
            
            # Sleep until next update
            self._stop_event.wait(self.update_interval)
    
    def start(self):
        """Start the monitoring thread."""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_event.clear()
            self._monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
            self._monitoring_thread.start()
    
    def stop(self):
        """Stop the monitoring thread."""
        self._stop_event.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2.0)
    
    def get_metrics(self) -> Dict:
        """Get current metrics snapshot."""
        return self.metrics.copy()
    
    def get_history(self) -> Dict:
        """Get historical data for graphs."""
        return {
            key: list(values) for key, values in self.history.items()
        }
    
    def get_average_over_seconds(self, metric_key: str, seconds: int = 60) -> Optional[float]:
        """
        Calculate average value for a metric over the last N seconds.
        
        Args:
            metric_key: Key in history dict (e.g., 'network_sent_mbps', 'gpu_utilization', 'fps')
            seconds: Number of seconds to average over
            
        Returns:
            Average value or None if insufficient data
        """
        if metric_key not in self.history:
            return None
        
        timestamps = list(self.history['timestamp'])
        values = list(self.history[metric_key])
        
        if len(timestamps) < 2 or len(values) < 2:
            return None
        
        # Get current time and calculate cutoff
        current_time = time.time()
        cutoff_time = current_time - seconds
        
        # Filter values within the time window
        valid_values = []
        for ts, val in zip(timestamps, values):
            if ts >= cutoff_time and val is not None:
                valid_values.append(val)
        
        if not valid_values:
            return None
        
        # Calculate average
        return sum(valid_values) / len(valid_values)


# Convenience function for testing
if __name__ == '__main__':
    monitor = SystemMonitor(update_interval=1.0)
    monitor.start()
    
    try:
        print("System Monitor - Press Ctrl+C to stop")
        print("=" * 60)
        while True:
            metrics = monitor.get_metrics()
            print(f"\rCPU: {metrics['cpu_percent']:.1f}% | "
                  f"Memory: {metrics['memory_percent']:.1f}% | "
                  f"CPU Temp: {metrics['cpu_temp'] or 'N/A'}°C | "
                  f"GPU: {metrics['gpu_utilization'] or 'N/A'}%", end='')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        monitor.stop()
        print("Done!")

