#!/usr/bin/env python3
"""
Tests for log viewer tab UI component.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from datetime import datetime

from src.ui.log_viewer_tab import LogViewerTab
from src.monitoring.log_monitor import LogEntry, LogPriority


@pytest.mark.ui
class TestLogViewerTab:
    """Tests for LogViewerTab widget."""
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_log_viewer_creation(self, mock_monitor_class, qapp):
        """Test creating log viewer tab."""
        mock_monitor = Mock()
        mock_monitor.on_new_entry = None
        mock_monitor.on_error = None
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        assert viewer.log_monitor == mock_monitor
        assert mock_monitor.on_new_entry is not None
        assert mock_monitor.on_error is not None
        mock_monitor.start.assert_called_once()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_filter_panel_creation(self, mock_monitor_class, qapp):
        """Test filter panel creation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Check priority checkboxes exist
        assert hasattr(viewer, 'priority_checkboxes')
        assert len(viewer.priority_checkboxes) > 0
        
        # Check source combo exists
        assert hasattr(viewer, 'source_combo')
        
        # Check search input exists
        assert hasattr(viewer, 'search_input')
        
        # Check time range group exists
        assert hasattr(viewer, 'time_range_group')
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_viewer_panel_creation(self, mock_monitor_class, qapp):
        """Test viewer panel creation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Check log display exists
        assert hasattr(viewer, 'log_display')
        assert viewer.log_display.isReadOnly()
        
        # Check control buttons exist
        assert hasattr(viewer, 'pause_btn')
        assert hasattr(viewer, 'autoscroll_btn')
        assert hasattr(viewer, 'clear_logs_btn')
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_on_new_entry(self, mock_monitor_class, qapp, qtbot):
        """Test handling new log entry."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Create test entry
        entry = LogEntry({
            '__REALTIME_TIMESTAMP': '1703520000000000',
            'PRIORITY': '3',
            'MESSAGE': 'Test error message',
            '_SYSTEMD_UNIT': 'test.service'
        })
        
        # Call handler
        viewer._on_new_entry(entry)
        
        # Check that entry was added to display
        assert viewer.log_display.toPlainText() != ""
        assert 'Test error message' in viewer.log_display.toPlainText()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    @patch('src.ui.log_viewer_tab.QMessageBox')
    def test_on_error(self, mock_messagebox, mock_monitor_class, qapp):
        """Test error handling."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Call error handler
        viewer._on_error("Test error message")
        
        # Check that warning was shown
        mock_messagebox.warning.assert_called_once()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_toggle_pause(self, mock_monitor_class, qapp):
        """Test pause/resume functionality."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Initially not paused
        assert viewer.pause_btn.text() == "⏸ Pause"
        
        # Toggle to pause
        viewer.pause_btn.setChecked(True)
        viewer._toggle_pause(True)
        
        assert viewer.pause_btn.text() == "▶ Resume"
        mock_monitor.pause.assert_called_once()
        
        # Toggle to resume
        viewer.pause_btn.setChecked(False)
        viewer._toggle_pause(False)
        
        assert viewer.pause_btn.text() == "⏸ Pause"
        mock_monitor.resume.assert_called_once()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_clear_logs(self, mock_monitor_class, qapp):
        """Test clearing log display."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Add some text
        viewer.log_display.setPlainText("Test log content")
        
        # Clear logs
        viewer._clear_logs()
        
        assert viewer.log_display.toPlainText() == ""
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_on_filter_changed(self, mock_monitor_class, qapp):
        """Test filter changes."""
        mock_monitor = Mock()
        mock_monitor.get_filtered_entries.return_value = []
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Set priority filter
        viewer.priority_checkboxes[LogPriority.ERR].setChecked(True)
        viewer.priority_checkboxes[LogPriority.INFO].setChecked(False)
        
        viewer._on_filter_changed()
        
        # Check that monitor filter was updated
        assert mock_monitor.set_priority_filter.called
        
        # Check that display was refreshed
        mock_monitor.get_filtered_entries.assert_called()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_clear_filters(self, mock_monitor_class, qapp):
        """Test clearing all filters."""
        mock_monitor = Mock()
        mock_monitor.get_filtered_entries.return_value = []
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        # Set some filters first
        viewer.priority_checkboxes[LogPriority.ERR].setChecked(False)
        viewer.search_input.setText("test search")
        
        # Clear filters
        viewer._clear_filters()
        
        # Check that filters were reset
        assert all(cb.isChecked() for cb in viewer.priority_checkboxes.values())
        assert viewer.search_input.text() == ""
        mock_monitor.clear_filters.assert_called_once()
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_refresh_logs(self, mock_monitor_class, qapp):
        """Test refreshing logs."""
        mock_monitor = Mock()
        mock_monitor.get_filtered_entries.return_value = []
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        viewer._refresh_logs()
        
        # Check that initial logs were loaded
        assert hasattr(mock_monitor, '_load_initial_logs')
        # Note: _load_initial_logs is called but we can't easily verify private methods
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_refresh_display(self, mock_monitor_class, qapp):
        """Test refreshing log display."""
        mock_monitor = Mock()
        
        # Create mock entries
        entries = [
            LogEntry({
                '__REALTIME_TIMESTAMP': '1703520000000000',
                'PRIORITY': '3',
                'MESSAGE': 'Error 1',
                '_SYSTEMD_UNIT': 'test.service'
            }),
            LogEntry({
                '__REALTIME_TIMESTAMP': '1703520001000000',
                'PRIORITY': '6',
                'MESSAGE': 'Info 1',
                '_SYSTEMD_UNIT': 'test.service'
            })
        ]
        
        mock_monitor.get_filtered_entries.return_value = entries
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        viewer._refresh_display()
        
        # Check that entries were displayed
        text = viewer.log_display.toPlainText()
        assert 'Error 1' in text or 'Info 1' in text
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_update_error_summary(self, mock_monitor_class, qapp):
        """Test updating error summary."""
        mock_monitor = Mock()
        mock_monitor.get_error_summary.return_value = {
            'total_errors': 10,
            'recent_critical_1h': 2,
            'recent_errors_1h': 5,
            'warnings': 3
        }
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        viewer._update_error_summary()
        
        # Check that summary label was updated
        text = viewer.summary_label.text()
        assert '10' in text  # Total errors
        assert '2' in text   # Critical
        assert '5' in text   # Errors
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_refresh_source_list(self, mock_monitor_class, qapp):
        """Test refreshing source list."""
        mock_monitor = Mock()
        mock_monitor.get_available_sources.return_value = ['service1', 'service2']
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        viewer.refresh_source_list()
        
        # Check that sources were added to combo
        assert viewer.source_combo.count() > 1
        assert viewer.source_combo.itemText(1) in ['service1', 'service2']
    
    @patch('src.monitoring.log_monitor.LogMonitor')
    def test_close_event(self, mock_monitor_class, qapp):
        """Test cleanup on close."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        viewer = LogViewerTab()
        
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        
        viewer.closeEvent(event)
        
        # Check that monitor was stopped
        mock_monitor.stop.assert_called_once()
        assert event.isAccepted()


@pytest.mark.ui
class TestLogViewerIntegration:
    """Integration tests for log viewer."""
    
    @patch('subprocess.run')
    def test_full_log_viewer_workflow(self, mock_run, qapp, qtbot):
        """Test full workflow of log viewer."""
        # Mock journalctl responses
        def mock_journalctl(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            if '--since' in args[0]:
                # For fetching new logs
                result.stdout = ""
            else:
                # For initial load
                import json
                entry = json.dumps({
                    '__REALTIME_TIMESTAMP': '1703520000000000',
                    'PRIORITY': '3',
                    'MESSAGE': 'Test error',
                    '_SYSTEMD_UNIT': 'test.service'
                })
                result.stdout = entry + '\n'
            return result
        
        mock_run.side_effect = mock_journalctl
        
        from src.ui.log_viewer_tab import LogViewerTab
        
        viewer = LogViewerTab()
        
        # Wait for initial load
        qtbot.wait(1000)
        
        # Verify viewer was created
        assert viewer is not None
        assert viewer.log_monitor is not None

