#!/usr/bin/env python3
"""
PSD TO FUSION CONVERTER v9.1 - DARK MODE GUI (FIXED)
Removed problematic drag-and-drop, using click-to-browse only
"""

import os
import re
import sys
import threading
import argparse
from PIL import Image
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: tkinter not available, falling back to CLI mode")

# Modern Dark Theme Colors
COLORS = {
    'bg_primary': '#0d1117',      # Main background
    'bg_secondary': '#161b22',    # Card/secondary background
    'bg_tertiary': '#21262d',     # Input fields
    'border': '#30363d',          # Borders
    'border_hover': '#8b949e',    # Hover borders
    'text_primary': '#f0f6fc',    # Main text
    'text_secondary': '#8b949e',  # Muted text
    'accent': '#58a6ff',          # Primary accent (blue)
    'accent_hover': '#79c0ff',     # Accent hover
    'success': '#238636',         # Green
    'success_hover': '#2ea043',    # Green hover
    'warning': '#d29922',         # Orange/Yellow
    'error': '#da3633',           # Red
    'error_hover': '#f85149',      # Red hover
}

class ModernButton(tk.Canvas):
    """Custom rounded button with hover effects"""
    def __init__(self, parent, text, command=None, width=120, height=36, 
                 bg_color=None, hover_color=None, text_color=None, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS['bg_secondary'], highlightthickness=0, **kwargs)
        
        self.bg_color = bg_color or COLORS['accent']
        self.hover_color = hover_color or COLORS['accent_hover']
        self.text_color = text_color or COLORS['text_primary']
        self.command = command
        self.text = text
        
        self.radius = 6
        self.current_bg = self.bg_color
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
        self.bind('<ButtonRelease-1>', self.on_release)
        
        self.draw()
        
    def draw(self):
        self.delete('all')
        # Draw rounded rectangle
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(), 
                                self.radius, fill=self.current_bg, outline='')
        # Draw text
        self.create_text(self.winfo_reqwidth()/2, self.winfo_reqheight()/2,
                        text=self.text, fill=self.text_color, 
                        font=('Segoe UI', 10, 'bold'))
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, e):
        self.current_bg = self.hover_color
        self.draw()
        self.config(cursor='hand2')
    
    def on_leave(self, e):
        self.current_bg = self.bg_color
        self.draw()
        self.config(cursor='')
    
    def on_click(self, e):
        self.current_bg = self.bg_color
        self.draw()
    
    def on_release(self, e):
        self.current_bg = self.hover_color
        self.draw()
        if self.command:
            self.command()

class ModernCheckbutton(tk.Frame):
    """Custom checkbox with modern styling"""
    def __init__(self, parent, text, variable=None, command=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_secondary'], **kwargs)
        
        self.variable = variable or tk.BooleanVar()
        self.command = command
        
        self.canvas = tk.Canvas(self, width=20, height=20, bg=COLORS['bg_secondary'],
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        
        self.label = tk.Label(self, text=text, bg=COLORS['bg_secondary'],
                             fg=COLORS['text_secondary'], font=('Segoe UI', 10))
        self.label.pack(side=tk.LEFT)
        
        self.checked = False
        self.draw_checkbox()
        
        self.canvas.bind('<Button-1>', self.toggle)
        self.label.bind('<Button-1>', self.toggle)
        self.bind('<Button-1>', self.toggle)
        
    def draw_checkbox(self):
        self.canvas.delete('all')
        # Draw box
        self.canvas.create_rectangle(2, 2, 18, 18, fill=COLORS['bg_tertiary'],
                                  outline=COLORS['border'], width=2)
        if self.checked:
            # Draw checkmark
            self.canvas.create_line(5, 10, 9, 14, fill=COLORS['accent'], width=2)
            self.canvas.create_line(9, 14, 15, 6, fill=COLORS['accent'], width=2)
            self.canvas.create_rectangle(2, 2, 18, 18, outline=COLORS['accent'], width=2)
    
    def toggle(self, e=None):
        self.checked = not self.checked
        self.variable.set(self.checked)
        self.draw_checkbox()
        if self.command:
            self.command()
    
    def get(self):
        return self.checked
    
    def set(self, value):
        self.checked = value
        self.variable.set(value)
        self.draw_checkbox()

class DropZone(tk.Frame):
    """Click-to-browse file zone (drag-and-drop removed for compatibility)"""
    def __init__(self, parent, on_select, **kwargs):
        super().__init__(parent, bg=COLORS['bg_tertiary'], highlightbackground=COLORS['border'],
                        highlightthickness=2, **kwargs)
        
        self.on_select = on_select
        self.configure(height=150)
        
        self.inner_frame = tk.Frame(self, bg=COLORS['bg_tertiary'])
        self.inner_frame.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)
        
        self.icon_label = tk.Label(self.inner_frame, text="📁", font=('Segoe UI', 32),
                                  bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        self.icon_label.pack(pady=(20, 10))
        
        self.text_label = tk.Label(self.inner_frame, text="Click to select PSD file",
                                  bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'],
                                  font=('Segoe UI', 11))
        self.text_label.pack()
        
        self.file_label = tk.Label(self.inner_frame, text="",
                                  bg=COLORS['bg_tertiary'], fg=COLORS['accent'],
                                  font=('Segoe UI', 9))
        self.file_label.pack(pady=(10, 0))
        
        # Bind click events to all children
        for widget in [self, self.inner_frame, self.icon_label, self.text_label, self.file_label]:
            widget.bind('<Button-1>', self.on_click)
            widget.bind('<Enter>', self.on_enter)
            widget.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        self.config(highlightbackground=COLORS['accent'])
        self.config(cursor='hand2')
        
    def on_leave(self, e):
        self.config(highlightbackground=COLORS['border'])
        self.config(cursor='')
        
    def on_click(self, e=None):
        file_path = filedialog.askopenfilename(
            title="Select PSD file",
            filetypes=[("Photoshop files", "*.psd"), ("All files", "*.*")]
        )
        if file_path:
            self.set_file(file_path)
            if self.on_select:
                self.on_select(file_path)
    
    def set_file(self, path):
        self.file_label.config(text=os.path.basename(path))
        self.text_label.config(text="File selected:")
        
    def clear(self):
        self.file_label.config(text="")
        self.text_label.config(text="Click to select PSD file")

class PSDConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PSD to Fusion Converter")
        self.root.geometry("700x600")
        self.root.configure(bg=COLORS['bg_primary'])
        self.root.minsize(600, 500)
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.rasterize_text = tk.BooleanVar(value=False)
        self.is_converting = False
        
        self.setup_styles()
        self.create_widgets()
        
        # Handle command line args if provided
        self.process_cli_args()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for dark theme
        style.configure('TFrame', background=COLORS['bg_primary'])
        style.configure('TLabel', background=COLORS['bg_primary'], 
                      foreground=COLORS['text_primary'], font=('Segoe UI', 10))
        style.configure('TEntry', fieldbackground=COLORS['bg_tertiary'],
                       foreground=COLORS['text_primary'], insertcolor=COLORS['text_primary'])
        
    def create_widgets(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header = tk.Frame(main_container, bg=COLORS['bg_primary'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header, text="PSD to Fusion Converter", 
                        bg=COLORS['bg_primary'], fg=COLORS['text_primary'],
                        font=('Segoe UI', 20, 'bold'))
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(header, text="Convert Photoshop files to DaVinci Fusion compositions",
                           bg=COLORS['bg_primary'], fg=COLORS['text_secondary'],
                           font=('Segoe UI', 11))
        subtitle.pack(anchor=tk.W, pady=(5, 0))
        
        # Card container
        card = tk.Frame(main_container, bg=COLORS['bg_secondary'], 
                       highlightbackground=COLORS['border'], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=10)
        card.configure(padx=20, pady=20)
        
        # Drop Zone (now click only)
        drop_frame = tk.Frame(card, bg=COLORS['bg_secondary'])
        drop_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.drop_zone = DropZone(drop_frame, on_select=self.on_file_selected)
        self.drop_zone.pack(fill=tk.X)
        
        # Options Section
        options_frame = tk.LabelFrame(card, text=" Conversion Options ", 
                                     bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                                     font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.FLAT,
                                     highlightbackground=COLORS['border'], highlightthickness=1)
        options_frame.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        # Output directory selection
        output_frame = tk.Frame(options_frame, bg=COLORS['bg_secondary'])
        output_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        output_label = tk.Label(output_frame, text="Output Folder:", 
                               bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                               font=('Segoe UI', 9))
        output_label.pack(anchor=tk.W)
        
        output_input_frame = tk.Frame(output_frame, bg=COLORS['bg_secondary'])
        output_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.output_entry = tk.Entry(output_input_frame, 
                                    bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                    insertbackground=COLORS['text_primary'],
                                    relief=tk.FLAT, font=('Segoe UI', 10))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10)
        
        browse_btn = ModernButton(output_input_frame, text="Browse", width=80, height=32,
                                 bg_color=COLORS['bg_tertiary'], 
                                 hover_color=COLORS['border'],
                                 text_color=COLORS['text_secondary'],
                                 command=self.browse_output)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Rasterize checkbox
        checkbox_frame = tk.Frame(options_frame, bg=COLORS['bg_secondary'])
        checkbox_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        self.rasterize_check = ModernCheckbutton(checkbox_frame, 
                                                text="Rasterize text layers (export as PNG images)",
                                                variable=self.rasterize_text)
        self.rasterize_check.pack(anchor=tk.W)
        
        # Hint text
        hint_frame = tk.Frame(options_frame, bg=COLORS['bg_secondary'])
        hint_frame.pack(fill=tk.X, padx=15, pady=(5, 0))
        
        hint_text = ("• Editable: Creates TextPlus nodes in Fusion (can modify text)\n"
                    "• Rasterized: Exports text as PNG (preserves exact appearance, not editable)")
        hint_label = tk.Label(hint_frame, text=hint_text, justify=tk.LEFT,
                             bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                             font=('Segoe UI', 9))
        hint_label.pack(anchor=tk.W)
        
        # Convert Button
        button_frame = tk.Frame(card, bg=COLORS['bg_secondary'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.convert_btn = ModernButton(button_frame, text="Convert to Fusion", 
                                       width=200, height=45,
                                       bg_color=COLORS['success'],
                                       hover_color=COLORS['success_hover'],
                                       command=self.start_conversion)
        self.convert_btn.pack(pady=10)
        
        # Status/Log Section
        log_frame = tk.LabelFrame(card, text=" Status Log ", 
                                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                                 font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.FLAT,
                                 highlightbackground=COLORS['border'], highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 bg=COLORS['bg_tertiary'],
                                                 fg=COLORS['text_primary'],
                                                 insertbackground=COLORS['text_primary'],
                                                 font=('Consolas', 9),
                                                 relief=tk.FLAT, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Footer
        footer = tk.Frame(main_container, bg=COLORS['bg_primary'])
        footer.pack(fill=tk.X, pady=(20, 0))
        
        footer_text = tk.Label(footer, text="v9.1 • Dark Mode Edition", 
                              bg=COLORS['bg_primary'], fg=COLORS['text_secondary'],
                              font=('Segoe UI', 9))
        footer_text.pack(side=tk.RIGHT)
        
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            
    def on_file_selected(self, file_path):
        self.input_file.set(file_path)
        # Auto-set output dir if not set
        if not self.output_entry.get():
            default_output = os.path.splitext(file_path)[0] + "_fusion"
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, default_output)
        self.log(f"Selected: {os.path.basename(file_path)}")
        
    def log(self, message, tag=None):
        self.log_text.config(state=tk.NORMAL)
        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def start_conversion(self):
        if self.is_converting:
            return
            
        input_path = self.input_file.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid PSD file first.")
            return
            
        output_path = self.output_entry.get()
        if not output_path:
            output_path = os.path.splitext(input_path)[0] + "_fusion"
            
        rasterize = self.rasterize_text.get()
        
        # Run conversion in thread to keep UI responsive
        self.is_converting = True
        self.convert_btn.config(state=tk.DISABLED)
        self.log("\n" + "="*50)
        self.log("Starting conversion...", "info")
        self.log(f"Mode: {'Rasterized' if rasterize else 'Editable'} text")
        
        thread = threading.Thread(target=self.run_conversion, 
                                 args=(input_path, output_path, rasterize))
        thread.daemon = True
        thread.start()
        
    def run_conversion(self, input_path, output_path, rasterize):
        try:
            # Redirect print to log
            import io
            import contextlib
            
            log_capture = io.StringIO()
            
            with contextlib.redirect_stdout(log_capture):
                result = convert_psd_to_comp(input_path, output_path, rasterize)
            
            # Get captured output and display in log
            output = log_capture.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self.root.after(0, lambda l=line: self.log(l))
            
            if result:
                self.root.after(0, lambda: self.log(f"\n✅ Success! Saved to: {result}"))
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Conversion complete!\n\nSaved to:\n{result}"))
            else:
                self.root.after(0, lambda: self.log("❌ Conversion failed", "error"))
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error: {str(e)}", "error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_converting = False
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))
            
    def process_cli_args(self):
        # Check if files were passed via command line
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            if os.path.exists(input_file) and input_file.lower().endswith('.psd'):
                self.root.after(100, lambda: self.on_file_selected(input_file))
                if len(sys.argv) > 2:
                    self.root.after(100, lambda: self.output_entry.insert(0, sys.argv[2]))

def sanitize_name(name):
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    if clean[0].isdigit():
        clean = "_" + clean
    return clean

def get_unique_name(base_name, existing_names):
    if base_name not in existing_names:
        return base_name
    counter = 1
    while f"{base_name}_{counter}" in existing_names:
        counter += 1
    return f"{base_name}_{counter}"

def export_layer_image(layer, output_path, psd_width, psd_height):
    try:
        canvas = Image.new('RGBA', (psd_width, psd_height), (0, 0, 0, 0))
        if hasattr(layer, 'composite'):
            layer_img = layer.composite()
        elif hasattr(layer, 'topil'):
            layer_img = layer.topil()
        else:
            return False
            
        if layer_img.mode != 'RGBA':
            layer_img = layer_img.convert('RGBA')
        
        left = int(getattr(layer, 'left', 0))
        top = int(getattr(layer, 'top', 0))
        canvas.paste(layer_img, (left, top), layer_img)
        canvas.save(output_path, 'PNG')
        return True
    except Exception as e:
        print(f"    Warning: Could not export {layer.name}: {e}")
        return False

def flatten_group(group_layer, psd_width, psd_height):
    try:
        canvas = Image.new('RGBA', (psd_width, psd_height), (0, 0, 0, 0))
        if hasattr(group_layer, 'composite'):
            group_img = group_layer.composite()
            if group_img:
                if group_img.mode != 'RGBA':
                    group_img = group_img.convert('RGBA')
                left = int(getattr(group_layer, 'left', 0))
                top = int(getattr(group_layer, 'top', 0))
                canvas.paste(group_img, (left, top), group_img)
        return canvas
    except:
        return None

def generate_comp_file(layers, psd_width, psd_height, output_dir, rasterize_text=False):
    comp_template = """Composition {\tCurrentTime = 0,
\tRenderRange = { 0, 1000 },
\tGlobalRange = { 0, 1000 },
\tCurrentID = %d,
\tPlaybackUpdateMode = 0,
\tVersion = "1.2",
\tSavedOutputs = 0,
\tHeldTools = 0,
\tDisabledTools = 0,
\tLockedTools = 0,
\tAudioOffset = 0,
\tResX = %d,
\tResY = %d,
\tPlaybackFrames = 0,
\tPlaybackTime = 0,
\tTransportState = 0,
\tCurrentTool = "MediaOut1",
\tTools = {
%s
\t},
\tViews = {
\t\t{
\t\t\tFrameTypeID = "FlowView",
\t\t\tMode = 0,
\t\t\tViewOffsetX = 0,
\t\t\tViewOffsetY = 0,
\t\t\tViewScale = 1
\t\t}
\t}
}"""

    tools_section = []
    existing_names = set()
    tool_id = 1
    
    Y_LOADER = 150
    Y_TRANSFORM = 75
    Y_MERGE = 0
    X_SPACING = 200

    canvas_def = f"""\t\tMasterCanvas = Background {{
\t\t\tInputs = {{
\t\t\t\tGlobalOut = Input {{ Value = 1000, }},
\t\t\t\tWidth = Input {{ Value = {psd_width}, }},
\t\t\t\tHeight = Input {{ Value = {psd_height}, }},
\t\t\t\tTopLeftAlpha = Input {{ Value = 0, }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ 0, {Y_MERGE} }},
\t\t\t}},
\t\t}},"""
    tools_section.append({"name": "MasterCanvas", "def": canvas_def, "id": tool_id})
    tool_id += 1
    
    prev_merge_name = "MasterCanvas"
    node_idx = 0
    
    for i, layer in enumerate(layers):
        if not layer.get("visible", True):
            continue
            
        layer_name_raw = str(layer["name"])
        layer_name = get_unique_name(sanitize_name(layer_name_raw), existing_names)
        existing_names.add(layer_name)
        
        current_x = (node_idx + 1) * X_SPACING
        node_idx += 1
        
        is_text_layer = layer["type"] == "TEXT"
        
        if is_text_layer and not rasterize_text and layer.get("text"):
            t = layer["text"]
            text_content = str(t["content"]).replace('"', '\\"').replace("\n", "\\n")
            
            pixel_height = float(t.get("pixel_height", 50.0))
            fusion_size = pixel_height / psd_height
            
            tool_def = f"""\t\t{layer_name} = TextPlus {{
\t\t\tCtrlWZoom = false,
\t\t\tInputs = {{
\t\t\t\tGlobalOut = Input {{ Value = 1000, }},
\t\t\t\tStyledText = Input {{ Value = "{text_content}", }},
\t\t\t\tFont = Input {{ Value = "Arial", }},
\t\t\t\tSize = Input {{ Value = {fusion_size}, }},
\t\t\t\tCenter = Input {{ Value = {{ 0.5, 0.5 }}, }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {current_x}, {Y_LOADER} }},
\t\t\t}},
\t\t}},"""
        else:
            if is_text_layer:
                img_filename = f"layer_{i:03d}_{sanitize_name(layer_name_raw)}_text.png"
            else:
                img_filename = f"layer_{i:03d}_{sanitize_name(layer_name_raw)}.png"
                
            img_path = os.path.abspath(os.path.join(output_dir, "layers", img_filename))
            img_path_lua = img_path.replace('\\', '\\\\')
            
            tool_def = f"""\t\t{layer_name} = Loader {{
\t\t\tCtrlWZoom = false,
\t\t\tClips = {{
\t\t\t\tClip {{
\t\t\t\t\tID = "Clip1",
\t\t\t\t\tFilename = "{img_path_lua}",
\t\t\t\t\tFormatID = "PNGFormat",
\t\t\t\t\tLength = 0,
\t\t\t\t\tLengthSetManually = true,
\t\t\t\t\tGlobalStart = 0,
\t\t\t\t\tGlobalEnd = 0
\t\t\t\t}}
\t\t\t}},
\t\t\tInputs = {{
\t\t\t\t["Clip1.PNGFormat.PostMultiply"] = Input {{ Value = 1, }},
\t\t\t\tGlobalOut = Input {{ Value = 1000, }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {current_x}, {Y_LOADER} }},
\t\t\t}},
\t\t}},"""
            layer["export_filename"] = img_filename
            if is_text_layer:
                layer["needs_export"] = True
        
        tools_section.append({"name": layer_name, "def": tool_def, "id": tool_id})
        tool_id += 1
        
        transform_name = get_unique_name(f"Transform_{layer_name}", existing_names)
        existing_names.add(transform_name)
        
        bbox = layer.get("bbox", [0, 0, psd_width, psd_height])
        
        if is_text_layer and not rasterize_text:
            cx = ((bbox[0] + bbox[2]) / 2) / psd_width
            cy = 1 - ((bbox[1] + bbox[3]) / 2) / psd_height
        else:
            cx, cy = 0.5, 0.5 
            
        transform_def = f"""\t\t{transform_name} = Transform {{
\t\t\tCtrlWZoom = false,
\t\t\tInputs = {{
\t\t\t\tCenter = Input {{ Value = {{ {cx:.6f}, {cy:.6f} }}, }},
\t\t\t\tInput = Input {{ SourceOp = "{layer_name}", Source = "Output", }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {current_x}, {Y_TRANSFORM} }},
\t\t\t}},
\t\t}},"""
        
        tools_section.append({"name": transform_name, "def": transform_def, "id": tool_id})
        tool_id += 1
        
        blend_mode = str(layer.get("blend_mode", "Normal"))
        opacity = float(layer.get("opacity", 1.0))
        
        blend_map = {
            "NORMAL": "Normal", "MULTIPLY": "Multiply", "SCREEN": "Screen", 
            "OVERLAY": "Overlay", "SOFT_LIGHT": "Soft Light", "HARD_LIGHT": "Hard Light"
        }
        fusion_blend = blend_map.get(blend_mode.upper(), "Normal")
        
        merge_name = get_unique_name(f"Merge_{layer_name}", existing_names)
        existing_names.add(merge_name)
        
        merge_def = f"""\t\t{merge_name} = Merge {{
\t\t\tCtrlWZoom = false,
\t\t\tInputs = {{
\t\t\t\tBackground = Input {{ SourceOp = "{prev_merge_name}", Source = "Output", }},
\t\t\t\tForeground = Input {{ SourceOp = "{transform_name}", Source = "Output", }},
\t\t\t\tApplyMode = Input {{ Value = "{fusion_blend}", }},
\t\t\t\tBlend = Input {{ Value = {opacity:.3f}, }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {current_x}, {Y_MERGE} }},
\t\t\t}},
\t\t}},"""
        
        tools_section.append({"name": merge_name, "def": merge_def, "id": tool_id})
        tool_id += 1
        prev_merge_name = merge_name
    
    if prev_merge_name:
        final_x = (node_idx + 1) * X_SPACING
        mediaout_def = f"""\t\tMediaOut1 = MediaOut {{
\t\t\tCtrlWZoom = false,
\t\t\tInputs = {{
\t\t\t\tInput = Input {{ SourceOp = "{prev_merge_name}", Source = "Output", }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {final_x}, {Y_MERGE} }},
\t\t\t}},
\t\t}},"""
        tools_section.append({"name": "MediaOut1", "def": mediaout_def, "id": tool_id})
        tool_id += 1
    
    tools_str = "\n".join([t["def"] for t in tools_section])
    comp_content = comp_template % (tool_id + 1, int(psd_width), int(psd_height), tools_str)
    
    return comp_content

def convert_psd_to_comp(psd_path, output_dir=None, rasterize_text=False):
    if not output_dir:
        output_dir = os.path.splitext(psd_path)[0] + "_fusion"
    
    output_dir = os.path.abspath(output_dir)
    layers_dir = os.path.join(output_dir, "layers")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(layers_dir, exist_ok=True)
    
    print(f"Converting: {psd_path}")
    print(f"Text handling: {'RASTERIZED (PNG)' if rasterize_text else 'EDITABLE (TextPlus)'}")
    
    try:
        from psd_tools import PSDImage
        from psd_tools.api.layers import PixelLayer, ShapeLayer, SmartObjectLayer, Group, TypeLayer
        
        psd = PSDImage.open(psd_path)
        psd_width, psd_height = psd.width, psd.height
        
        layers = []
        
        def extract_layers(group):
            for layer in group:
                if isinstance(layer, Group):
                    is_visible = bool(layer.visible) if hasattr(layer, 'visible') else True
                    if is_visible:
                        extract_layers(layer)
                elif isinstance(layer, TypeLayer):
                    bbox = [float(getattr(layer, 'left', 0)), float(getattr(layer, 'top', 0)), 
                           float(getattr(layer, 'right', psd_width)), float(getattr(layer, 'bottom', psd_height))]
                    
                    actual_height = abs(bbox[3] - bbox[1])
                    if actual_height < 5:
                        actual_height = 50
                        
                    layer_data = {
                        "name": str(layer.name),
                        "visible": bool(layer.visible) if hasattr(layer, 'visible') else True,
                        "opacity": float(layer.opacity) / 255.0 if hasattr(layer, 'opacity') else 1.0,
                        "blend_mode": str(layer.blend_mode).split('.')[-1] if hasattr(layer, 'blend_mode') else 'NORMAL',
                        "bbox": bbox,
                        "type": "TEXT",
                    }
                    try:
                        text_content = str(layer.text).replace('\r', '\n') if hasattr(layer, 'text') else str(layer.name)
                    except:
                        text_content = str(layer.name)
                        
                    layer_data["text"] = {"content": text_content, "pixel_height": actual_height}
                    layers.append(layer_data)
                elif isinstance(layer, (PixelLayer, ShapeLayer, SmartObjectLayer)):
                    layer_data = {
                        "name": str(layer.name),
                        "visible": bool(layer.visible) if hasattr(layer, 'visible') else True,
                        "opacity": float(layer.opacity) / 255.0 if hasattr(layer, 'opacity') else 1.0,
                        "blend_mode": str(layer.blend_mode).split('.')[-1] if hasattr(layer, 'blend_mode') else 'NORMAL',
                        "bbox": [float(getattr(layer, 'left', 0)), float(getattr(layer, 'top', 0)), 
                                float(getattr(layer, 'right', psd_width)), float(getattr(layer, 'bottom', psd_height))],
                        "type": "RASTER",
                        "layer_obj": layer
                    }
                    layers.append(layer_data)
        
        extract_layers(psd)
        
        print("\nExporting layer images...")
        for i, layer in enumerate(layers):
            if not layer.get("visible", True):
                continue
                
            should_export = False
            img_filename = None
            
            if layer["type"] == "RASTER":
                should_export = True
                img_filename = f"layer_{i:03d}_{sanitize_name(layer['name'])}.png"
            elif layer["type"] == "TEXT" and rasterize_text:
                should_export = True
                img_filename = f"layer_{i:03d}_{sanitize_name(layer['name'])}_text.png"
                print(f"  📝 Rasterizing text layer: {layer['name']}")
            
            if should_export:
                img_path = os.path.join(layers_dir, img_filename)
                
                if layer.get("is_group"):
                    group_img = flatten_group(layer.get("layer_obj"), psd_width, psd_height)
                    if group_img:
                        group_img.save(img_path, 'PNG')
                        print(f"  ✓ Group -> {img_filename}")
                else:
                    layer_obj = layer.get("layer_obj")
                    if layer_obj:
                        if export_layer_image(layer_obj, img_path, psd_width, psd_height):
                            print(f"  ✓ Layer -> {img_filename}")
                    elif layer["type"] == "TEXT" and rasterize_text:
                        for psd_layer in psd.descendants():
                            if isinstance(psd_layer, TypeLayer) and psd_layer.name == layer["name"]:
                                if export_layer_image(psd_layer, img_path, psd_width, psd_height):
                                    print(f"  ✓ Text (rasterized) -> {img_filename}")
                                break
        
        comp_content = generate_comp_file(layers, psd_width, psd_height, output_dir, rasterize_text)
        comp_path = os.path.join(output_dir, "composition.comp")
        with open(comp_path, 'w', encoding='utf-8') as f:
            f.write(comp_content)
        
        print(f"\n✅ SUCCESS! Saved: {comp_path}")
        print(f"   Mode: {'Rasterized text (PNG images)' if rasterize_text else 'Editable text (TextPlus nodes)'}")
        return comp_path
        
    except ImportError:
        print("ERROR: psd-tools not installed. Run: pip install psd-tools pillow")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise

def cli_main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Convert PSD to DaVinci Fusion .comp file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python psd_to_fusion.py                    # Launch GUI
  python psd_to_fusion.py input.psd -r       # CLI mode: Rasterize text
  python psd_to_fusion.py input.psd -o out   # CLI mode: Custom output
        """
    )
    
    parser.add_argument("input", nargs='?', help="Path to input PSD file")
    parser.add_argument("-o", "--output", help="Output directory (default: input_fusion/)")
    parser.add_argument("-r", "--rasterize-text", action="store_true", 
                        help="Rasterize text layers to PNG instead of creating editable TextPlus nodes")
    parser.add_argument("--cli", action="store_true", 
                        help="Force CLI mode even if GUI is available")
    
    args = parser.parse_args()
    
    # If no input provided or GUI available and not forced CLI, launch GUI
    if not args.input and TKINTER_AVAILABLE:
        root = tk.Tk()
        app = PSDConverterGUI(root)
        root.mainloop()
    elif args.input and (args.cli or not TKINTER_AVAILABLE):
        # CLI mode
        if not os.path.exists(args.input):
            print(f"Error: File not found: {args.input}")
            sys.exit(1)
        convert_psd_to_comp(args.input, args.output, args.rasterize_text)
    elif args.input and TKINTER_AVAILABLE:
        # GUI mode with pre-loaded file
        root = tk.Tk()
        app = PSDConverterGUI(root)
        # File will be processed by process_cli_args
        root.mainloop()
    else:
        print("Error: No input file specified and GUI not available")
        print("Install tkinter for GUI mode or provide input file")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()