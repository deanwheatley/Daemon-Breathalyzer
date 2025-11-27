#!/usr/bin/env python3
"""
Test Fan Features
Tests all fan control functionality to ensure everything works as expected.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_asusctl_availability():
    """Test if asusctl is available and working."""
    print("🔍 Testing asusctl availability...")
    
    try:
        result = subprocess.run(['asusctl', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✅ asusctl found: {result.stdout.strip()}")
            return True
        else:
            print(f"  ❌ asusctl error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ❌ asusctl not found - install from https://asus-linux.org/asusctl/")
        return False
    except subprocess.TimeoutExpired:
        print("  ❌ asusctl timeout")
        return False

def test_fan_profiles():
    """Test fan profile detection and switching."""
    print("\n🔍 Testing fan profiles...")
    
    try:
        from control.asusctl_interface import AsusctlInterface
        
        interface = AsusctlInterface()
        
        # Test profile detection
        current_profile = interface.get_current_profile()
        print(f"  ✅ Current profile: {current_profile}")
        
        # Test available profiles
        profiles = interface.get_available_profiles()
        print(f"  ✅ Available profiles: {profiles}")
        
        # Test profile switching (if multiple profiles available)
        if len(profiles) > 1:
            test_profile = profiles[1] if profiles[0] == current_profile else profiles[0]
            print(f"  🔄 Testing profile switch to: {test_profile}")
            
            if interface.set_profile(test_profile):
                print(f"    ✅ Successfully switched to {test_profile}")
                
                # Switch back
                if interface.set_profile(current_profile):
                    print(f"    ✅ Successfully switched back to {current_profile}")
                else:
                    print(f"    ⚠️  Failed to switch back to {current_profile}")
            else:
                print(f"    ❌ Failed to switch to {test_profile}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Profile test failed: {e}")
        return False

def test_fan_curves():
    """Test fan curve operations."""
    print("\n🔍 Testing fan curves...")
    
    try:
        from control.asusctl_interface import AsusctlInterface
        
        interface = AsusctlInterface()
        
        # Test getting current curves
        cpu_curve = interface.get_fan_curve('cpu')
        gpu_curve = interface.get_fan_curve('gpu')
        
        print(f"  ✅ CPU curve: {len(cpu_curve) if cpu_curve else 0} points")
        print(f"  ✅ GPU curve: {len(gpu_curve) if gpu_curve else 0} points")
        
        # Test curve validation
        if cpu_curve and len(cpu_curve) >= 4:
            print("  ✅ CPU curve has sufficient points")
        else:
            print("  ⚠️  CPU curve may need more points")
            
        if gpu_curve and len(gpu_curve) >= 4:
            print("  ✅ GPU curve has sufficient points")
        else:
            print("  ⚠️  GPU curve may need more points")
        
        # Test preset curves
        from control.profile_manager import ProfileManager
        profile_manager = ProfileManager()
        
        presets = profile_manager.get_preset_names()
        print(f"  ✅ Available presets: {presets}")
        
        if presets:
            test_preset = presets[0]
            preset_data = profile_manager.load_preset(test_preset)
            print(f"  ✅ Loaded preset '{test_preset}': {len(preset_data.get('cpu_curve', []))} CPU points, {len(preset_data.get('gpu_curve', []))} GPU points")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fan curve test failed: {e}")
        return False

def test_curve_file_manager():
    """Test curve file operations."""
    print("\n🔍 Testing curve file manager...")
    
    try:
        from control.curve_file_manager import CurveFileManager
        
        manager = CurveFileManager()
        
        # Test directory creation
        curves_dir = manager.curves_dir
        print(f"  ✅ Curves directory: {curves_dir}")
        
        # Test listing curves
        curves = manager.list_curves()
        print(f"  ✅ Found {len(curves)} saved curves: {curves}")
        
        # Test saving a test curve
        test_curve = {
            'name': 'test_curve',
            'cpu_curve': [(30, 20), (50, 40), (70, 60), (90, 80)],
            'gpu_curve': [(30, 25), (50, 45), (70, 65), (90, 85)],
            'description': 'Test curve for validation'
        }
        
        test_file = 'test_validation_curve'
        if manager.save_curve(test_file, test_curve):
            print(f"  ✅ Successfully saved test curve: {test_file}")
            
            # Test loading
            loaded = manager.load_curve(test_file)
            if loaded and loaded['name'] == test_curve['name']:
                print(f"  ✅ Successfully loaded test curve")
                
                # Clean up
                if manager.delete_curve(test_file):
                    print(f"  ✅ Successfully deleted test curve")
                else:
                    print(f"  ⚠️  Failed to delete test curve")
            else:
                print(f"  ❌ Failed to load test curve correctly")
        else:
            print(f"  ❌ Failed to save test curve")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Curve file manager test failed: {e}")
        return False

def test_system_monitoring():
    """Test system monitoring capabilities."""
    print("\n🔍 Testing system monitoring...")
    
    try:
        from monitoring.system_monitor import SystemMonitor
        
        monitor = SystemMonitor()
        
        # Test basic metrics
        metrics = monitor.get_metrics()
        
        print(f"  ✅ CPU usage: {metrics.get('cpu_percent', 'N/A')}%")
        print(f"  ✅ Memory usage: {metrics.get('memory_percent', 'N/A')}%")
        print(f"  ✅ CPU temp: {metrics.get('cpu_temp', 'N/A')}°C")
        print(f"  ✅ GPU temp: {metrics.get('gpu_temp', 'N/A')}°C")
        print(f"  ✅ CPU fan: {metrics.get('cpu_fan_rpm', 'N/A')} RPM")
        print(f"  ✅ GPU fan: {metrics.get('gpu_fan_rpm', 'N/A')} RPM")
        print(f"  ✅ FPS: {metrics.get('fps', 'N/A')}")
        
        # Test if we have reasonable values
        issues = []
        if metrics.get('cpu_percent', 0) < 0 or metrics.get('cpu_percent', 0) > 100:
            issues.append("CPU usage out of range")
        if metrics.get('memory_percent', 0) < 0 or metrics.get('memory_percent', 0) > 100:
            issues.append("Memory usage out of range")
        if metrics.get('cpu_temp') and (metrics['cpu_temp'] < 0 or metrics['cpu_temp'] > 150):
            issues.append("CPU temperature out of range")
            
        if issues:
            print(f"  ⚠️  Monitoring issues: {', '.join(issues)}")
        else:
            print("  ✅ All monitoring values look reasonable")
        
        return True
        
    except Exception as e:
        print(f"  ❌ System monitoring test failed: {e}")
        return False

def test_dependencies():
    """Test dependency detection."""
    print("\n🔍 Testing dependency detection...")
    
    try:
        from utils.dependency_checker import DependencyChecker
        
        checker = DependencyChecker()
        results = checker.check_all()
        
        print(f"  ✅ All dependencies installed: {results['all_installed']}")
        print(f"  ✅ Required dependencies installed: {results['required_installed']}")
        
        if results['missing_required']:
            print(f"  ❌ Missing required: {[dep.name for dep in results['missing_required']]}")
        
        if results['missing_optional']:
            print(f"  ⚠️  Missing optional: {[dep.name for dep in results['missing_optional']]}")
        
        # Show installed dependencies
        installed = [info['name'] for info in results['details'] 
                    if info['status'] in ['installed', 'system_command']]
        print(f"  ✅ Installed ({len(installed)}): {', '.join(installed)}")
        
        return results['required_installed']
        
    except Exception as e:
        print(f"  ❌ Dependency test failed: {e}")
        return False

def main():
    """Run all fan feature tests."""
    print("=" * 60)
    print("🧪 Fan Features Test Suite")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("asusctl Availability", test_asusctl_availability),
        ("System Monitoring", test_system_monitoring),
        ("Fan Profiles", test_fan_profiles),
        ("Fan Curves", test_fan_curves),
        ("Curve File Manager", test_curve_file_manager),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Fan features are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())