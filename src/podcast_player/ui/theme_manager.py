"""
Theme Manager for Podcast Player

Provides theme switching capabilities including light and dark modes.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
import json
from pathlib import Path


class ThemeManager:
    """Manages UI themes for the application."""
    
    def __init__(self, config_manager=None):
        """
        Initialize theme manager.
        
        Args:
            config_manager: ConfigManager instance for persistence
        """
        self.config_manager = config_manager
        self.current_theme = "light"
        self.root: Optional[tk.Tk] = None # Add root attribute
        
        # Define theme configurations
        self.themes = {
            "light": {
                "name": "淺色主題",
                "colors": {
                    "bg_primary": "#ffffff",
                    "bg_secondary": "#f0f0f0", 
                    "bg_tertiary": "#e0e0e0",
                    "fg_primary": "#000000",
                    "fg_secondary": "#333333",
                    "accent": "#0078d4",
                    "accent_hover": "#106ebe",
                    "success": "#107c10",
                    "warning": "#ff8c00",
                    "error": "#d13438",
                    "border": "#cccccc",
                    "selection": "#0078d4",
                    "selection_bg": "#cce8ff"
                },
                "fonts": {
                    "default": ("Arial", 10),
                    "title": ("Arial", 14, "bold"),
                    "button": ("Arial", 10),
                    "menu": ("Arial", 9)
                }
            },
            "dark": {
                "name": "深色主題",
                "colors": {
                    "bg_primary": "#2b2b2b",
                    "bg_secondary": "#383838",
                    "bg_tertiary": "#404040",
                    "fg_primary": "#ffffff",
                    "fg_secondary": "#e0e0e0",
                    "accent": "#0ea5e9",
                    "accent_hover": "#0284c7",
                    "success": "#22c55e",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "border": "#555555",
                    "selection": "#0ea5e9",
                    "selection_bg": "#1e3a5f"
                },
                "fonts": {
                    "default": ("Arial", 10),
                    "title": ("Arial", 14, "bold"),
                    "button": ("Arial", 10),
                    "menu": ("Arial", 9)
                }
            }
        }
        
        # Load saved theme preference
        self._load_theme_preference()
    
    def get_available_themes(self) -> Dict[str, str]:
        """
        Get list of available themes.
        
        Returns:
            Dictionary mapping theme IDs to display names
        """
        return {theme_id: theme_data["name"] for theme_id, theme_data in self.themes.items()}
    
    def get_current_theme(self) -> str:
        """
        Get current theme ID.
        
        Returns:
            Current theme ID
        """
        return self.current_theme
    
    def set_theme(self, theme_id: str) -> bool:
        """
        Set current theme.
        
        Args:
            theme_id: Theme ID to set
            
        Returns:
            True if theme was set successfully, False otherwise
        """
        if theme_id not in self.themes:
            print(f"Theme '{theme_id}' not found")
            return False
        
        self.current_theme = theme_id
        self._save_theme_preference()
        return True
    
    def get_color(self, color_key: str) -> str:
        """
        Get color value for current theme.
        
        Args:
            color_key: Color key to look up
            
        Returns:
            Color value (hex string)
        """
        theme_data = self.themes.get(self.current_theme, self.themes["light"])
        return theme_data["colors"].get(color_key, "#000000")
    
    def get_font(self, font_key: str) -> tuple:
        """
        Get font configuration for current theme.
        
        Args:
            font_key: Font key to look up
            
        Returns:
            Font tuple (family, size, *style)
        """
        theme_data = self.themes.get(self.current_theme, self.themes["light"])
        return theme_data["fonts"].get(font_key, ("Arial", 10))
    
    def apply_theme_to_widget(self, widget: tk.Widget, widget_type: str = "default") -> None:
        """
        Apply current theme to a specific widget.
        
        Args:
            widget: Widget to apply theme to
            widget_type: Type of widget for specific styling
        """
        try:
            theme_colors = self.themes[self.current_theme]["colors"]
            
            # Skip TTK widgets - they are handled separately
            if hasattr(widget, 'winfo_class') and widget.winfo_class().startswith('T'):
                return
            
            # Common configurations for different widget types
            if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
                widget.configure(bg=theme_colors["bg_primary"])
            
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=theme_colors["bg_secondary"])
            
            elif isinstance(widget, tk.Label):
                widget.configure(
                    bg=theme_colors["bg_secondary"],
                    fg=theme_colors["fg_primary"],
                    font=self.get_font("default")
                )
            
            elif isinstance(widget, tk.Button):
                widget.configure(
                    bg=theme_colors["accent"],
                    fg=theme_colors["fg_primary"],
                    activebackground=theme_colors["accent_hover"],
                    activeforeground=theme_colors["fg_primary"],
                    font=self.get_font("button"),
                    relief="flat",
                    borderwidth=1
                )
            
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg=theme_colors["bg_primary"],
                    fg=theme_colors["fg_primary"],
                    insertbackground=theme_colors["fg_primary"],
                    relief="solid",
                    borderwidth=1,
                    highlightcolor=theme_colors["accent"]
                )
            
            elif isinstance(widget, tk.Text):
                widget.configure(
                    bg=theme_colors["bg_primary"],
                    fg=theme_colors["fg_primary"],
                    insertbackground=theme_colors["fg_primary"],
                    selectbackground=theme_colors["selection_bg"],
                    selectforeground=theme_colors["fg_primary"]
                )
            
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    bg=theme_colors["bg_primary"],
                    fg=theme_colors["fg_primary"],
                    selectbackground=theme_colors["selection_bg"],
                    selectforeground=theme_colors["fg_primary"],
                    relief="solid",
                    borderwidth=1
                )
                
        except Exception as e:
            print(f"Error applying theme to widget: {e}")
    
    def apply_theme_to_ttk_widgets(self, style: ttk.Style) -> None:
        """
        Apply current theme to TTK widgets using style configuration.
        
        Args:
            style: TTK Style instance
        """
        try:
            theme_colors = self.themes[self.current_theme]["colors"]
            
            # Configure TTK styles
            style.theme_use('clam')  # Use clam theme as base for better customization
            
            # Button styles
            style.configure(
                "TButton",
                background=theme_colors["accent"],
                foreground=theme_colors["fg_primary"],
                borderwidth=1,
                focuscolor='none'
            )
            style.map(
                "TButton",
                background=[('active', theme_colors["accent_hover"]),
                           ('pressed', theme_colors["accent_hover"])]
            )
            
            # Entry styles
            style.configure(
                "TEntry",
                fieldbackground=theme_colors["bg_primary"],
                foreground=theme_colors["fg_primary"],
                bordercolor=theme_colors["border"],
                lightcolor=theme_colors["bg_secondary"],
                darkcolor=theme_colors["bg_secondary"]
            )
            style.map(
                "TEntry",
                focuscolor=[('focus', theme_colors["accent"])]
            )
            
            # Combobox styles
            style.configure(
                "TCombobox",
                fieldbackground=theme_colors["bg_primary"],
                foreground=theme_colors["fg_primary"],
                background=theme_colors["bg_secondary"]
            )
            
            # Frame styles
            style.configure(
                "TFrame",
                background=theme_colors["bg_secondary"]
            )
            
            # Label styles
            style.configure(
                "TLabel",
                background=theme_colors["bg_secondary"],
                foreground=theme_colors["fg_primary"]
            )
            
            # Progressbar styles
            style.configure(
                "TProgressbar",
                background=theme_colors["accent"],
                troughcolor=theme_colors["bg_tertiary"],
                borderwidth=1,
                lightcolor=theme_colors["accent"],
                darkcolor=theme_colors["accent"]
            )
            
            # Scale (slider) styles
            style.configure(
                "TScale",
                background=theme_colors["bg_secondary"],
                troughcolor=theme_colors["bg_tertiary"],
                slidercolor=theme_colors["accent"]
            )
            
            # Treeview styles
            style.configure(
                "Treeview",
                background=theme_colors["bg_primary"],
                foreground=theme_colors["fg_primary"],
                fieldbackground=theme_colors["bg_primary"],
                borderwidth=1
            )
            style.configure(
                "Treeview.Heading",
                background=theme_colors["bg_tertiary"],
                foreground=theme_colors["fg_primary"],
                relief="flat"
            )
            style.map(
                "Treeview",
                background=[('selected', theme_colors["selection_bg"])],
                foreground=[('selected', theme_colors["fg_primary"])]
            )
            
        except Exception as e:
            print(f"Error applying TTK theme: {e}")
    
    def apply_theme_to_application(self, root: tk.Tk, widgets: Dict[str, Any]) -> None:
        """
        Apply current theme to entire application.
        
        Args:
            root: Root window
            widgets: Dictionary of application widgets
        """
        if not root.winfo_exists(): # Check if root window still exists
            return
        
        try:
            # Apply to root window
            if isinstance(root, tk.Widget): # Ensure it's a Widget type
                self.apply_theme_to_widget(root)
            
            # Configure TTK style
            style = ttk.Style()
            self.apply_theme_to_ttk_widgets(style)
            
            # Apply to all registered widgets
            if isinstance(root, tk.Widget): # Ensure it's a Widget type
                self._apply_theme_recursively(root)
            
        except Exception as e:
            print(f"Error applying theme to application: {e}")
    
    def _apply_theme_recursively(self, widget: tk.Widget) -> None:
        """
        Recursively apply theme to widget and all its children.
        
        Args:
            widget: Widget to apply theme to
        """
        if not widget.winfo_exists(): # Check if widget still exists
            return

        try:
            # Apply theme to current widget
            if isinstance(widget, tk.Widget): # Ensure it's a Widget type
                self.apply_theme_to_widget(widget)
            
            # Apply to all children
            for child in widget.winfo_children():
                if isinstance(child, tk.Widget): # Ensure it's a Widget type
                    self._apply_theme_recursively(child)
                
        except Exception as e:
            print(f"Error in recursive theme application: {e}")
    
    def _load_theme_preference(self) -> None:
        """Load saved theme preference from config."""
        try:
            if self.config_manager:
                saved_theme = self.config_manager.get_setting("theme", "light")
                if saved_theme in self.themes:
                    self.current_theme = saved_theme
        except Exception as e:
            print(f"Error loading theme preference: {e}")
            self.current_theme = "light"
    
    def _save_theme_preference(self) -> None:
        """Save current theme preference to config."""
        try:
            if self.config_manager:
                self.config_manager.set_setting("theme", self.current_theme)
        except Exception as e:
            print(f"Error saving theme preference: {e}")
    
    def toggle_theme(self) -> str:
        """
        Toggle between light and dark themes.
        
        Returns:
            New theme ID
        """
        if self.current_theme == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")
        
        return self.current_theme
    
    def create_theme_menu(self, parent_menu: tk.Menu) -> tk.Menu:
        """
        Create theme selection submenu.
        
        Args:
            parent_menu: Parent menu to add theme menu to
            
        Returns:
            Created theme menu
        """
        theme_menu = tk.Menu(parent_menu, tearoff=0)
        
        for theme_id, theme_name in self.get_available_themes().items():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=tk.StringVar(value=self.current_theme),
                value=theme_id,
                command=lambda t=theme_id: self.set_theme(t)
            )
        
        return theme_menu
