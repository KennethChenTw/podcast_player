"""
Preferences Dialog for Podcast Player

Provides user interface for adjusting application preferences including font scaling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class PreferencesDialog:
    """Preferences dialog for application settings."""
    
    def __init__(self, parent: tk.Widget, config_manager, font_manager, 
                 apply_callback: Optional[Callable] = None):
        """
        Initialize preferences dialog.
        
        Args:
            parent: Parent widget
            config_manager: ConfigManager instance
            font_manager: FontManager instance
            apply_callback: Callback function when settings are applied
        """
        self.parent = parent
        self.config_manager = config_manager
        self.font_manager = font_manager
        self.apply_callback = apply_callback
        
        # Dialog window
        self.dialog = None
        
        # Settings variables
        self.font_scale_var = tk.DoubleVar()
        self.font_scale_percentage_var = tk.StringVar()
        
        # Preview label for font scaling
        self.preview_label = None
        
    def show(self) -> None:
        """Show the preferences dialog."""
        if self.dialog:
            self.dialog.lift()
            return
            
        self._create_dialog()
        self._load_current_settings()
        self._center_dialog()
        
    def _create_dialog(self) -> None:
        """Create the dialog window and widgets."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("偏好設定")
        
        # Calculate responsive dialog size
        base_width, base_height = 400, 300
        current_scale = self.font_manager.scale
        
        # Dialog size scales more conservatively than font
        size_scale = 1.0 + (current_scale - 1.0) * 0.4
        dialog_width = int(base_width * size_scale)
        dialog_height = int(base_height * size_scale)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.resizable(True, True)  # Allow resizing for large fonts
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different preference categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Appearance tab
        appearance_frame = ttk.Frame(notebook, padding="10")
        notebook.add(appearance_frame, text="外觀")
        
        self._create_appearance_tab(appearance_frame)
        
        # Button frame with responsive padding
        current_scale = self.font_manager.scale
        base_pady = 10
        responsive_pady = self.font_manager.get_responsive_padding(base_pady)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(responsive_pady, 0))
        
        # Buttons with responsive spacing
        base_padx = 5
        responsive_padx = self.font_manager.get_responsive_padding(base_padx)
        
        ttk.Button(button_frame, text="確定", command=self._on_ok).pack(side=tk.RIGHT, padx=(responsive_padx, 0))
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="套用", command=self._on_apply).pack(side=tk.RIGHT, padx=(0, responsive_padx))
        ttk.Button(button_frame, text="重設", command=self._on_reset).pack(side=tk.LEFT)
        
    def _create_appearance_tab(self, parent: ttk.Frame) -> None:
        """Create the appearance preferences tab."""
        # Font scaling section
        font_frame = ttk.LabelFrame(parent, text="字體大小", padding="10")
        font_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Font scale label and percentage
        scale_info_frame = ttk.Frame(font_frame)
        scale_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(scale_info_frame, text="字體縮放:").pack(side=tk.LEFT)
        
        # Percentage label
        percentage_label = ttk.Label(scale_info_frame, textvariable=self.font_scale_percentage_var)
        percentage_label.pack(side=tk.RIGHT)
        
        # Font scale slider
        scale_frame = ttk.Frame(font_frame)
        scale_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(scale_frame, text="60%").pack(side=tk.LEFT)
        
        self.font_scale_slider = ttk.Scale(
            scale_frame,
            from_=0.6,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.font_scale_var,
            command=self._on_font_scale_change
        )
        self.font_scale_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Label(scale_frame, text="200%").pack(side=tk.RIGHT)
        
        # Preview section
        preview_frame = ttk.LabelFrame(font_frame, text="預覽", padding="10")
        preview_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.preview_label = ttk.Label(
            preview_frame,
            text="這是字體大小的預覽文字\\nFont size preview text",
            justify=tk.CENTER
        )
        # Apply current font scale to preview
        current_scale = self.font_manager.scale
        self.font_manager.configure_widget_font(self.preview_label, 'content')
        self.preview_label.pack()
        
    def _load_current_settings(self) -> None:
        """Load current settings into the dialog."""
        # Load font scale
        current_scale = self.config_manager.get_font_scale()
        self.font_scale_var.set(current_scale)
        self._update_font_scale_display(current_scale)
        
    def _center_dialog(self) -> None:
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
        
    def _on_font_scale_change(self, value: str) -> None:
        """Handle font scale slider change."""
        scale = float(value)
        self._update_font_scale_display(scale)
        self._update_preview(scale)
        
    def _update_font_scale_display(self, scale: float) -> None:
        """Update font scale percentage display."""
        percentage = int(scale * 100)
        self.font_scale_percentage_var.set(f"{percentage}%")
        
    def _update_preview(self, scale: float) -> None:
        """Update preview label with new font scale."""
        if self.preview_label:
            # Temporarily update font manager scale for preview
            original_scale = self.font_manager.scale
            self.font_manager.set_scale(scale)
            
            # Apply the scaled font to preview
            self.font_manager.configure_widget_font(self.preview_label, 'content')
            
            # Restore original scale
            self.font_manager.set_scale(original_scale)
            
    def _on_ok(self) -> None:
        """Handle OK button click."""
        self._apply_settings()
        self._close_dialog()
        
    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self._close_dialog()
        
    def _on_apply(self) -> None:
        """Handle Apply button click."""
        self._apply_settings()
        
    def _on_reset(self) -> None:
        """Handle Reset button click."""
        # Reset to default values
        default_scale = 1.0
        self.font_scale_var.set(default_scale)
        self._update_font_scale_display(default_scale)
        self._update_preview(default_scale)
        
    def _apply_settings(self) -> None:
        """Apply current settings."""
        try:
            # Save font scale
            new_scale = self.font_scale_var.get()
            self.config_manager.set_font_scale(new_scale)
            
            # Update font manager
            self.font_manager.set_scale(new_scale)
            
            # Call apply callback if provided
            if self.apply_callback:
                self.apply_callback(new_scale)
                
            # Save configuration using the new basic settings method
            try:
                if hasattr(self.config_manager, 'save_basic_settings'):
                    self.config_manager.save_basic_settings()
                else:
                    print("Warning: save_basic_settings method not available")
                        
            except Exception as save_error:
                print(f"Warning: Could not save font scale to file: {save_error}")
                # Continue anyway - the setting is applied to the current session
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"套用設定時發生錯誤: {str(e)}")
            
    def _close_dialog(self) -> None:
        """Close the dialog."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None