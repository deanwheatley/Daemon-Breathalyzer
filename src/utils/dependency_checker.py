#!/usr/bin/env python3
"""
Dependency Checker and Installer

Checks for required dependencies and provides installation instructions.
"""

import subprocess
import sys
import importlib
import shutil
import re
from typing import Dict, List, Tuple, Optional
from enum import Enum


class DependencyStatus(Enum):
    """Status of a dependency."""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    SYSTEM_COMMAND = "system_command"  # System command (e.g., nvidia-smi)
    OPTIONAL = "optional"  # Optional dependency


class Dependency:
    """Represents a dependency to check."""
    
    def __init__(
        self,
        name: str,
        pip_package: Optional[str] = None,
        import_name: Optional[str] = None,
        system_command: Optional[str] = None,
        description: str = "",
        install_instructions: Optional[str] = None,
        is_optional: bool = False,
        check_function: Optional[callable] = None
    ):
        """
        Initialize a dependency.
        
        Args:
            name: Human-readable name
            pip_package: PyPI package name (if different from import name)
            import_name: Python import name (e.g., 'PyQt6')
            system_command: System command to check (e.g., 'nvidia-smi')
            description: Description of what this dependency provides
            install_instructions: Custom installation instructions
            is_optional: Whether this is an optional dependency
            check_function: Custom function to check availability
        """
        self.name = name
        self.pip_package = pip_package or import_name
        self.import_name = import_name
        self.system_command = system_command
        self.description = description
        self.install_instructions = install_instructions
        self.is_optional = is_optional
        self.check_function = check_function
        self.status = DependencyStatus.NOT_INSTALLED
        self.error_message = None


class DependencyChecker:
    """Checks and manages dependencies."""
    
    def __init__(self):
        """Initialize the dependency checker."""
        self.dependencies = self._initialize_dependencies()
        self.installable_via_pip = []
    
    def _initialize_dependencies(self) -> List[Dependency]:
        """Initialize the list of required dependencies."""
        deps = [
            # UI Framework
            Dependency(
                name="PyQt6",
                pip_package="PyQt6",
                import_name="PyQt6",
                description="Main UI framework for the application",
                install_instructions="pip install PyQt6"
            ),
            Dependency(
                name="PyQtGraph",
                pip_package="PyQtGraph",
                import_name="pyqtgraph",
                description="Real-time plotting library for graphs",
                install_instructions="pip install PyQtGraph"
            ),
            
            # System Monitoring
            Dependency(
                name="psutil",
                pip_package="psutil",
                import_name="psutil",
                description="System and process monitoring utilities",
                install_instructions="pip install psutil"
            ),
            Dependency(
                name="py3nvml",
                pip_package="py3nvml",
                import_name="py3nvml",
                description="NVIDIA GPU monitoring (optional - falls back to nvidia-smi)",
                install_instructions="pip install py3nvml",
                is_optional=True
            ),
            
            # Utilities
            Dependency(
                name="PyYAML",
                pip_package="PyYAML",
                import_name="yaml",
                description="YAML configuration file parsing",
                install_instructions="pip install PyYAML"
            ),
            
            # Hardware Control - ASUS
            Dependency(
                name="asusctl",
                system_command="asusctl",
                description="ASUS laptop control utility (required for ASUS fan control)",
                install_instructions="See: https://asus-linux.org/asusctl/",
                is_optional=True
            ),
            
            # GPU Drivers and Tools
            Dependency(
                name="nvidia-smi",
                system_command="nvidia-smi",
                description="NVIDIA GPU monitoring tool (optional - for NVIDIA GPU metrics)",
                install_instructions="sudo apt install nvidia-driver-535 nvidia-utils-535",
                is_optional=True
            ),
            
            # Hardware Sensors
            Dependency(
                name="sensors",
                system_command="sensors",
                description="Hardware sensor monitoring (optional - for better temperature readings)",
                install_instructions="sudo apt install lm-sensors && sudo sensors-detect",
                is_optional=True
            ),
            
            # Gaming and FPS Monitoring
            Dependency(
                name="MangoHud",
                system_command="mangohud",
                description="Gaming overlay for FPS monitoring (optional - enables accurate FPS detection)",
                install_instructions="sudo apt install mangohud",
                is_optional=True
            ),
            
            # Additional Hardware Support
            Dependency(
                name="dmidecode",
                system_command="dmidecode",
                description="Hardware information tool (optional - for motherboard detection)",
                install_instructions="sudo apt install dmidecode",
                is_optional=True
            ),
            Dependency(
                name="lspci",
                system_command="lspci",
                description="PCI device listing tool (optional - for hardware detection)",
                install_instructions="sudo apt install pciutils",
                is_optional=True
            ),
            
            # Fan Control Alternatives
            Dependency(
                name="fancontrol",
                system_command="fancontrol",
                description="Generic PWM fan control (optional - alternative to asusctl)",
                install_instructions="sudo apt install fancontrol",
                is_optional=True
            ),
            
            # Additional Monitoring Tools
            Dependency(
                name="radeontop",
                system_command="radeontop",
                description="AMD GPU monitoring tool (optional - for AMD GPU metrics)",
                install_instructions="sudo apt install radeontop",
                is_optional=True
            ),
            Dependency(
                name="intel_gpu_top",
                system_command="intel_gpu_top",
                description="Intel GPU monitoring tool (optional - for Intel GPU metrics)",
                install_instructions="sudo apt install intel-gpu-tools",
                is_optional=True
            ),
        ]
        
        return deps
    
    def check_all(self) -> Dict[str, any]:
        """
        Check all dependencies.
        
        Returns:
            Dictionary with status information:
            {
                'all_installed': bool,
                'required_installed': bool,
                'missing_required': List[Dependency],
                'missing_optional': List[Dependency],
                'details': List[Dict]
            }
        """
        missing_required = []
        missing_optional = []
        
        for dep in self.dependencies:
            dep.status = self._check_dependency(dep)
            
            if dep.status == DependencyStatus.NOT_INSTALLED:
                if dep.is_optional:
                    missing_optional.append(dep)
                else:
                    missing_required.append(dep)
        
        all_installed = len(missing_required) == 0 and len(missing_optional) == 0
        required_installed = len(missing_required) == 0
        
        return {
            'all_installed': all_installed,
            'required_installed': required_installed,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'details': [self._get_dep_info(dep) for dep in self.dependencies]
        }
    
    def _check_dependency(self, dep: Dependency) -> DependencyStatus:
        """Check if a dependency is available."""
        # Custom check function
        if dep.check_function:
            try:
                if dep.check_function():
                    return DependencyStatus.INSTALLED
                else:
                    return DependencyStatus.NOT_INSTALLED
            except:
                return DependencyStatus.NOT_INSTALLED
        
        # System command check
        if dep.system_command:
            if shutil.which(dep.system_command):
                return DependencyStatus.SYSTEM_COMMAND
            else:
                return DependencyStatus.NOT_INSTALLED
        
        # Python import check
        if dep.import_name:
            try:
                importlib.import_module(dep.import_name)
                return DependencyStatus.INSTALLED
            except ImportError:
                return DependencyStatus.NOT_INSTALLED
        
        return DependencyStatus.NOT_INSTALLED
    
    def _get_dep_info(self, dep: Dependency) -> Dict:
        """Get information about a dependency."""
        status_icon = {
            DependencyStatus.INSTALLED: "✅",
            DependencyStatus.SYSTEM_COMMAND: "✅",
            DependencyStatus.NOT_INSTALLED: "❌",
            DependencyStatus.OPTIONAL: "⚪"
        }
        
        return {
            'name': dep.name,
            'status': dep.status.value,
            'icon': status_icon.get(dep.status, "❓"),
            'description': dep.description,
            'install_instructions': dep.install_instructions,
            'pip_package': dep.pip_package,
            'is_optional': dep.is_optional,
            'system_command': dep.system_command,
            'error': dep.error_message
        }
    
    def can_install_via_pip(self, dep: Dependency) -> bool:
        """Check if a dependency can be installed via pip."""
        return dep.pip_package is not None and dep.system_command is None
    
    def install_via_pip(self, dep: Dependency) -> Tuple[bool, str]:
        """
        Attempt to install a dependency via pip.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.can_install_via_pip(dep):
            return False, "Cannot install via pip"
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep.pip_package],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, f"Successfully installed {dep.name}"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Installation failed: {error_msg[:200]}"
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_install_instructions(self, dep: Dependency) -> str:
        """Get formatted installation instructions for a dependency."""
        instructions = []
        
        instructions.append(f"## Installing {dep.name}")
        instructions.append(f"\n{dep.description}\n")
        
        if self.can_install_via_pip(dep):
            instructions.append(f"**Automated installation:**")
            instructions.append(f"```bash")
            instructions.append(f"pip install {dep.pip_package}")
            instructions.append(f"```\n")
        
        if dep.install_instructions:
            instructions.append(f"**Manual installation:**")
            if dep.install_instructions.startswith("sudo"):
                instructions.append(f"Run in terminal:")
            else:
                instructions.append(f"Run in terminal:")
            instructions.append(f"```bash")
            instructions.append(dep.install_instructions)
            instructions.append(f"```\n")
        
        # Special instructions for common dependencies
        if dep.name == "asusctl":
            instructions.append(f"\n**Detailed instructions:**")
            instructions.append(f"1. Visit: https://asus-linux.org/asusctl/")
            instructions.append(f"2. Follow the installation guide for your distribution")
            instructions.append(f"3. Ensure the asusd service is running: `sudo systemctl enable --now asusd`")
            instructions.append(f"4. Test with: `asusctl --version`\n")
        elif dep.name == "nvidia-smi":
            instructions.append(f"\n**NVIDIA Driver Installation:**")
            instructions.append(f"- Recommended: `sudo apt install nvidia-driver-535 nvidia-utils-535`")
            instructions.append(f"- Alternative: Download from https://www.nvidia.com/drivers")
            instructions.append(f"- Verify with: `nvidia-smi`")
            instructions.append(f"- Reboot after installation\n")
        elif dep.name == "sensors":
            instructions.append(f"\n**Hardware Sensors Setup:**")
            instructions.append(f"1. Install: `sudo apt install lm-sensors`")
            instructions.append(f"2. Detect sensors: `sudo sensors-detect` (answer yes to all)")
            instructions.append(f"3. Test: `sensors`")
            instructions.append(f"4. May require reboot for full functionality\n")
        elif dep.name == "MangoHud":
            instructions.append(f"\n**Gaming FPS Monitoring:**")
            instructions.append(f"1. Install: `sudo apt install mangohud`")
            instructions.append(f"2. Run games with: `mangohud %command%` (Steam) or `mangohud <game>`")
            instructions.append(f"3. FPS data will be automatically detected by the application")
            instructions.append(f"4. Configure in ~/.config/MangoHud/MangoHud.conf if needed\n")
        elif dep.name == "fancontrol":
            instructions.append(f"\n**Generic Fan Control Setup:**")
            instructions.append(f"1. Install: `sudo apt install fancontrol`")
            instructions.append(f"2. Configure: `sudo pwmconfig`")
            instructions.append(f"3. Enable service: `sudo systemctl enable fancontrol`")
            instructions.append(f"4. Alternative to asusctl for non-ASUS systems\n")
        elif dep.name in ["radeontop", "intel_gpu_top"]:
            instructions.append(f"\n**GPU Monitoring:**")
            instructions.append(f"- Provides detailed GPU usage and temperature monitoring")
            instructions.append(f"- Run with: `{dep.system_command}`")
            instructions.append(f"- May require adding user to video group: `sudo usermod -a -G video $USER`\n")
        
        return "\n".join(instructions)


def detect_hardware_specific_dependencies() -> List[str]:
    """Detect hardware-specific dependencies that should be installed."""
    additional_deps = []
    
    try:
        # Check for NVIDIA GPU
        result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'NVIDIA' in result.stdout or 'GeForce' in result.stdout:
                additional_deps.extend(['nvidia-driver-535', 'nvidia-utils-535'])
            if 'AMD' in result.stdout and 'Radeon' in result.stdout:
                additional_deps.extend(['mesa-vulkan-drivers', 'radeontop'])
            if 'Intel' in result.stdout and ('VGA' in result.stdout or '3D' in result.stdout):
                additional_deps.extend(['intel-media-va-driver', 'intel-gpu-tools'])
        
        # Check for ASUS motherboard
        result = subprocess.run(['sudo', 'dmidecode', '-t', 'baseboard'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and 'ASUS' in result.stdout.upper():
            if not shutil.which('asusctl'):
                print("⚠️  ASUS hardware detected but asusctl not installed")
                print("   Visit: https://asus-linux.org/asusctl/")
    
    except Exception:
        pass  # Hardware detection failed, continue without additional deps
    
    return additional_deps


# Convenience function for checking dependencies
def check_dependencies() -> Dict[str, any]:
    """Check all dependencies and return status."""
    checker = DependencyChecker()
    return checker.check_all()


if __name__ == '__main__':
    # Test the dependency checker
    checker = DependencyChecker()
    results = checker.check_all()
    
    print("Dependency Check Results")
    print("=" * 60)
    print(f"\nAll installed: {results['all_installed']}")
    print(f"Required installed: {results['required_installed']}")
    print(f"\nMissing required ({len(results['missing_required'])}):")
    for dep in results['missing_required']:
        print(f"  ❌ {dep.name}: {dep.description}")
    
    print(f"\nMissing optional ({len(results['missing_optional'])}):")
    for dep in results['missing_optional']:
        print(f"  ⚪ {dep.name}: {dep.description}")
    
    print(f"\nInstalled ({len(results['details']) - len(results['missing_required']) - len(results['missing_optional'])}):")
    for info in results['details']:
        if info['status'] != 'not_installed':
            print(f"  ✅ {info['name']}")


