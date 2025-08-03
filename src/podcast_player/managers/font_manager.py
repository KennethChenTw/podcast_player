"""
Font Manager for Podcast Player

Manages font scaling and provides consistent font configuration across the application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple, Optional


class FontManager:
    """Manages application fonts and scaling."""
    
    # 基礎字體大小定義
    BASE_FONT_SIZES = {
        'title': 14,
        'content': 10,
        'button': 12,
        'small': 8,
        'large': 16,
        'control': 10
    }
    
    # 預設字體家族
    DEFAULT_FONT_FAMILY = "Arial"
    
    def __init__(self, scale: float = 1.0):
        """
        Initialize font manager.
        
        Args:
            scale: Font scale factor (0.8 to 1.2 for phase 1)
        """
        self.scale = max(0.8, min(1.2, scale))  # 限制在 80%-120%
        self._font_cache = {}
        self._style = None
        
    def set_scale(self, scale: float) -> None:
        """
        Update font scale and clear cache.
        
        Args:
            scale: New font scale factor
        """
        self.scale = max(0.8, min(1.2, scale))
        self._font_cache.clear()
        
    def get_font(self, font_type: str, weight: str = "normal") -> Tuple[str, int, str]:
        """
        Get scaled font configuration.
        
        Args:
            font_type: Font type key from BASE_FONT_SIZES
            weight: Font weight ('normal', 'bold')
            
        Returns:
            Tuple of (family, size, weight)
        """
        cache_key = f"{font_type}_{weight}_{self.scale}"
        
        if cache_key not in self._font_cache:
            base_size = self.BASE_FONT_SIZES.get(font_type, 10)
            scaled_size = int(base_size * self.scale)
            
            self._font_cache[cache_key] = (self.DEFAULT_FONT_FAMILY, scaled_size, weight)
            
        return self._font_cache[cache_key]
    
    def get_scaled_size(self, base_size: int) -> int:
        """
        Get scaled size for custom values.
        
        Args:
            base_size: Base size in pixels
            
        Returns:
            Scaled size
        """
        return int(base_size * self.scale)
    
    def get_treeview_row_height(self) -> int:
        """
        Get appropriate TreeView row height for current scale.
        
        Returns:
            Row height in pixels
        """
        base_height = 20
        return self.get_scaled_size(base_height)
    
    def get_button_height(self) -> int:
        """
        Get appropriate button height for current scale.
        
        Returns:
            Button height in pixels
        """
        base_height = 30
        return self.get_scaled_size(base_height)
    
    def get_entry_height(self) -> int:
        """
        Get appropriate entry widget height for current scale.
        
        Returns:
            Entry height in pixels
        """
        base_height = 25
        return self.get_scaled_size(base_height)
    
    def apply_to_style(self, style: Optional[ttk.Style] = None) -> None:
        """
        Apply font scaling to ttk styles.
        
        Args:
            style: TTK Style instance, creates new if None
        """
        if style is None:
            style = ttk.Style()
        
        self._style = style
        
        # 套用各種元件的字體樣式
        style.configure("Play.TButton", font=self.get_font('button', 'bold'))
        style.configure("Control.TButton", font=self.get_font('control'))
        style.configure("Title.TLabel", font=self.get_font('title', 'bold'))
        style.configure("Info.TLabel", font=self.get_font('content'))
        
        # TreeView 樣式
        style.configure("Treeview", 
                       font=self.get_font('content'),
                       rowheight=self.get_treeview_row_height())
        style.configure("Treeview.Heading", font=self.get_font('content', 'bold'))
        
        # 其他元件樣式
        style.configure("TCombobox", font=self.get_font('content'))
        style.configure("TEntry", font=self.get_font('content'))
        style.configure("TButton", font=self.get_font('button'))
        style.configure("TLabel", font=self.get_font('content'))
    
    def configure_widget_font(self, widget: tk.Widget, font_type: str, weight: str = "normal") -> None:
        """
        Configure font for a specific widget.
        
        Args:
            widget: Tkinter widget to configure
            font_type: Font type key
            weight: Font weight
        """
        font_config = self.get_font(font_type, weight)
        
        try:
            widget.configure(font=font_config)
        except tk.TclError:
            # Widget may not support font configuration
            pass
    
    def get_scale_percentage(self) -> int:
        """
        Get current scale as percentage.
        
        Returns:
            Scale percentage (80-120)
        """
        return int(self.scale * 100)
    
    @classmethod
    def from_percentage(cls, percentage: int) -> 'FontManager':
        """
        Create FontManager from percentage.
        
        Args:
            percentage: Scale percentage (80-120)
            
        Returns:
            FontManager instance
        """
        scale = percentage / 100.0
        return cls(scale)