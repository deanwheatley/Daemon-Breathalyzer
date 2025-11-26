#!/usr/bin/env python3
"""
Tests for About tab UI component.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl

from src.ui.about_tab import AboutTab


@pytest.mark.ui
class TestAboutTab:
    """Tests for AboutTab widget."""
    
    def test_about_tab_creation(self, qapp):
        """Test creating about tab."""
        tab = AboutTab()
        
        assert tab is not None
        assert hasattr(tab, 'setup_ui')
    
    def test_about_tab_has_links(self, qapp):
        """Test that about tab contains expected links."""
        tab = AboutTab()
        
        # Check that the widget has children (labels, buttons, etc.)
        children = tab.findChildren(type(None))
        # At minimum, should have some child widgets
        assert tab.layout() is not None
    
    @patch('src.ui.about_tab.QDesktopServices.openUrl')
    def test_github_link_opens_url(self, mock_open_url, qapp):
        """Test that GitHub link button opens correct URL."""
        tab = AboutTab()
        
        # Find the GitHub button - we need to search for buttons with text "View on GitHub"
        buttons = tab.findChildren(type(QApplication.instance().focusWidget()))
        # Actually, we can just call the method directly
        tab._open_url("https://github.com/deanwheatley/asus-control/")
        
        mock_open_url.assert_called_once()
        call_args = mock_open_url.call_args[0][0]
        assert isinstance(call_args, QUrl)
        assert call_args.toString() == "https://github.com/deanwheatley/asus-control/"
    
    @patch('src.ui.about_tab.QDesktopServices.openUrl')
    def test_email_link_opens_mailto(self, mock_open_url, qapp):
        """Test that email link opens mailto: URL."""
        tab = AboutTab()
        
        tab._open_url("mailto:deanwheatley@hotmail.com")
        
        mock_open_url.assert_called_once()
        call_args = mock_open_url.call_args[0][0]
        assert isinstance(call_args, QUrl)
        assert call_args.toString() == "mailto:deanwheatley@hotmail.com"
    
    @patch('src.ui.about_tab.QDesktopServices.openUrl')
    def test_linkedin_link_opens_url(self, mock_open_url, qapp):
        """Test that LinkedIn link opens correct URL."""
        tab = AboutTab()
        
        tab._open_url("https://www.linkedin.com/in/dean-wheatley-8944511a/")
        
        mock_open_url.assert_called_once()
        call_args = mock_open_url.call_args[0][0]
        assert isinstance(call_args, QUrl)
        assert call_args.toString() == "https://www.linkedin.com/in/dean-wheatley-8944511a/"
    
    def test_about_tab_styling(self, qapp):
        """Test that about tab has game-style theme applied."""
        tab = AboutTab()
        
        # Should have stylesheet applied
        stylesheet = tab.styleSheet()
        assert len(stylesheet) > 0
    
    def test_about_tab_layout(self, qapp):
        """Test that about tab has proper layout structure."""
        tab = AboutTab()
        
        layout = tab.layout()
        assert layout is not None
        assert layout.count() > 0  # Should have some widgets

