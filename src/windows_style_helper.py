#!/usr/bin/env python
"""
Helper module for Windows-specific window styling.
This module provides utilities for setting dark title bars on Windows.
"""
import platform
import ctypes

class WindowsStyleHelper:
    """Helper for Windows-specific window styling"""
    
    @staticmethod
    def set_dark_title_bar(hwnd):
        """Enable dark title bar on Windows 10+"""
        if platform.system() == "Windows":
            try:
                # Windows 10 1809 or later
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                
                # Tell Windows to use dark mode for the title bar
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 
                    DWMWA_USE_IMMERSIVE_DARK_MODE, 
                    ctypes.byref(ctypes.c_int(1)), 
                    ctypes.sizeof(ctypes.c_int)
                )
                return True
            except Exception:
                return False
        return False 