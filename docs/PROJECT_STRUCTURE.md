# Fan Control UI - Project Structure

## 📁 Recommended Project Structure

### Option 1: Python + GTK4

```
asus-fan-control-ui/
├── README.md
├── requirements.txt
├── setup.py
├── pyproject.toml
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── src/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main window class
│   │   ├── dashboard.py     # Dashboard tab
│   │   ├── fan_curve_editor.py  # Fan curve editor
│   │   ├── settings.py      # Settings tab
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── metric_card.py    # Metric display widget
│   │       ├── graph_widget.py   # Real-time graph
│   │       └── fan_curve_graph.py # Interactive fan curve graph
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── system_monitor.py    # System metrics collection
│   │   ├── cpu_monitor.py       # CPU monitoring
│   │   ├── gpu_monitor.py       # GPU monitoring (NVIDIA)
│   │   └── sensor_monitor.py    # Temperature/fan sensors
│   ├── control/
│   │   ├── __init__.py
│   │   ├── asusctl_interface.py # asusctl integration
│   │   ├── fan_curve_manager.py  # Fan curve management
│   │   └── profile_manager.py    # Profile management
│   └── utils/
│       ├── __init__.py
│       ├── logger.py         # Logging utilities
│       └── validators.py     # Input validation
├── data/
│   ├── icons/               # Application icons
│   ├── themes/              # Theme files
│   └── presets/             # Default fan curve presets
├── tests/
│   ├── __init__.py
│   ├── test_monitoring.py
│   └── test_control.py
└── docs/
    ├── user_guide.md
    └── developer_guide.md
```

### Option 2: Python + PyQt6

```
asus-fan-control-ui/
├── README.md
├── requirements.txt
├── main.py                  # Entry point
├── ui/
│   ├── main_window.ui      # Qt Designer file (optional)
│   ├── main_window.py       # Main window
│   ├── dashboard_tab.py
│   ├── fan_curve_tab.py
│   └── settings_tab.py
├── core/
│   ├── monitor.py          # System monitoring
│   ├── controller.py       # Fan control
│   └── config.py           # Configuration
├── widgets/
│   ├── metric_widget.py
│   ├── graph_widget.py
│   └── fan_curve_widget.py
└── resources/
    ├── icons/
    └── styles/
```

## 🔧 Key Components

### 1. System Monitor (`monitoring/system_monitor.py`)

```python
class SystemMonitor:
    """Main system monitoring class"""
    
    def __init__(self, update_interval=1.0):
        self.update_interval = update_interval
        self.cpu_monitor = CPUMonitor()
        self.gpu_monitor = GPUMonitor()
        self.sensor_monitor = SensorMonitor()
        
    def start_monitoring(self):
        """Start monitoring loop"""
        
    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        
    def register_callback(self, callback):
        """Register callback for metric updates"""
```

### 2. Fan Curve Manager (`control/fan_curve_manager.py`)

```python
class FanCurveManager:
    """Manages fan curve configurations"""
    
    def __init__(self):
        self.asusctl = AsusctlInterface()
        
    def get_current_curves(self, profile: str) -> List[FanCurve]:
        """Get current fan curves for profile"""
        
    def set_fan_curve(self, profile: str, fan: str, curve: FanCurve):
        """Set fan curve via asusctl"""
        
    def validate_curve(self, curve: FanCurve) -> bool:
        """Validate fan curve"""
        
    def save_profile(self, name: str, curves: Dict[str, FanCurve]):
        """Save custom profile"""
```

### 3. Main Window (`ui/main_window.py`)

```python
class MainWindow(Gtk.ApplicationWindow):
    """Main application window"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.monitor = SystemMonitor()
        self.fan_manager = FanCurveManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI components"""
        
    def update_metrics(self):
        """Update displayed metrics"""
        
    def on_fan_curve_changed(self, curve):
        """Handle fan curve changes"""
```

### 4. Fan Curve Editor (`ui/fan_curve_editor.py`)

```python
class FanCurveEditor(Gtk.Box):
    """Interactive fan curve editor"""
    
    def __init__(self):
        self.canvas = FanCurveCanvas()
        self.control_points = []
        
    def add_control_point(self, temp: float, fan_speed: float):
        """Add control point to curve"""
        
    def remove_control_point(self, point):
        """Remove control point"""
        
    def update_curve(self):
        """Update curve visualization"""
        
    def get_curve(self) -> FanCurve:
        """Get current curve data"""
```

## 📦 Dependencies

### Python + GTK4 (`requirements.txt`)

```
# UI Framework
PyGObject>=3.42.0

# System Monitoring
psutil>=5.9.0
py3nvml>=0.2.6
pydbus>=0.6.0

# Data & Visualization
matplotlib>=3.6.0
numpy>=1.24.0

# Configuration
pyyaml>=6.0
toml>=0.10.2

# Utilities
python-systemd>=234
```

### Python + PyQt6 (`requirements.txt`)

```
# UI Framework
PyQt6>=6.4.0
PyQt6-Charts>=6.4.0

# System Monitoring
psutil>=5.9.0
py3nvml>=0.2.6

# Data & Visualization
PyQtGraph>=0.13.0
numpy>=1.24.0

# Configuration
pyyaml>=6.0
```

## 🚀 Getting Started Template

### `main.py` (GTK4)

```python
#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

from src.ui.main_window import MainWindow

class FanControlApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='com.asus.fancontrol',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
    def do_activate(self):
        win = MainWindow(self)
        win.present()

if __name__ == '__main__':
    app = FanControlApp()
    app.run()
```

### `main.py` (PyQt6)

```python
#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Daemon Breathalyzer")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
```

## 🔌 Integration Examples

### asusctl Integration

```python
import subprocess
import json

class AsusctlInterface:
    def get_fan_curves(self, profile: str):
        """Get fan curves for profile"""
        result = subprocess.run(
            ['asusctl', 'fan-curve', '--mod-profile', profile],
            capture_output=True, text=True
        )
        # Parse output and return curves
        
    def set_fan_curve(self, profile: str, fan: str, curve_data: str):
        """Set fan curve"""
        subprocess.run([
            'asusctl', 'fan-curve',
            '--mod-profile', profile,
            '--fan', fan,
            '--data', curve_data
        ])
        
    def enable_fan_curves(self, profile: str, enabled: bool):
        """Enable/disable fan curves"""
        subprocess.run([
            'asusctl', 'fan-curve',
            '--mod-profile', profile,
            '--enable-fan-curves', str(enabled).lower()
        ])
```

### System Monitoring

```python
import psutil
import subprocess

class CPUMonitor:
    def get_usage(self):
        return psutil.cpu_percent(interval=1)
        
    def get_temperature(self):
        # Read from /sys/class/thermal/
        # or use psutil.sensors_temperatures()
        pass
        
    def get_frequency(self):
        return psutil.cpu_freq().current

class GPUMonitor:
    def get_metrics(self):
        result = subprocess.run([
            'nvidia-smi',
            '--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True)
        
        # Parse and return metrics
        pass
```

## 📝 Next Steps

1. **Choose technology stack** (GTK4 or PyQt6)
2. **Set up project structure**
3. **Create basic monitoring module**
4. **Build simple UI with metrics display**
5. **Add fan curve editor**
6. **Integrate with asusctl**
7. **Add polish and features**

Would you like me to:
- Create a starter project with one of these structures?
- Implement the basic monitoring module?
- Build a simple UI prototype?
- Set up the development environment?

