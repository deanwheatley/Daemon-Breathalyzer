# Quick Start Guide

## Setup

1. **Create and activate virtual environment:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

From the project root directory:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
python src/main.py
```

Or from the `src/` directory:

```bash
python main.py
```

## What's Included

### ✅ Completed Features

1. **System Monitoring Module** (`src/monitoring/system_monitor.py`)
   - Real-time CPU usage and per-core monitoring
   - CPU temperature detection (multiple methods)
   - CPU frequency monitoring
   - Memory and swap usage
   - NVIDIA GPU monitoring (via py3nvml or nvidia-smi fallback)
   - GPU temperature, utilization, memory, and power
   - Fan speed detection
   - Historical data collection for graphs

2. **PyQt6 Main Window** (`src/ui/main_window.py`)
   - Modern tabbed interface
   - Dashboard tab with real-time metrics
   - Placeholder tabs for Fan Curves, Profiles, and Settings
   - Status bar with live updates

3. **Dashboard Widgets** (`src/ui/dashboard_widgets.py`)
   - MetricCard: Displays individual metrics with color coding
   - GraphWidget: Real-time graphs using PyQtGraph
   - Auto-updating visualizations

### 📊 Dashboard Metrics

The dashboard displays:
- **CPU**: Usage %, Temperature (°C), Frequency (MHz)
- **Memory**: Usage %, Used (GB)
- **GPU**: Usage %, Temperature (°C), Memory %

All metrics update every second with live graphs showing historical trends.

### 🔧 Next Steps

1. **Fan Curve Editor**: Implement the interactive fan curve editor tab
2. **asusctl Integration**: Connect to asusctl for fan control
3. **Profile Management**: Add profile save/load functionality
4. **Settings Panel**: Configure monitoring intervals, alerts, etc.

## Testing System Monitoring

You can test the monitoring module independently:

```bash
python src/monitoring/system_monitor.py
```

This will run a console version showing real-time metrics.

## Troubleshooting

### GPU Monitoring Not Working

- Ensure NVIDIA drivers are installed
- Try: `nvidia-smi` to verify GPU is accessible
- The module will automatically fall back to nvidia-smi command if py3nvml fails

### Temperature Not Showing

- Install `lm-sensors`: `sudo apt install lm-sensors`
- Run: `sudo sensors-detect`
- Check: `/sys/class/thermal/` for thermal zones

### Missing Dependencies

- Make sure virtual environment is activated
- Re-run: `pip install -r requirements.txt`

## Architecture

```
src/
├── main.py                 # Application entry point
├── monitoring/
│   └── system_monitor.py   # System metrics collection
└── ui/
    ├── main_window.py      # Main PyQt6 window
    └── dashboard_widgets.py # Reusable UI components
```


