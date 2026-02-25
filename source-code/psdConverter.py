#!/usr/bin/env python3
"""
PSD TO FUSION CONVERTER - DARK MODE & DRAG-AND-DROP UI
Uses the exact WORK3 path logic for media linking.
"""

import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image

# Import Drag and Drop library
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("WARNING: tkinterdnd2 not found. Drag and drop will be disabled.")
    print("To enable, run: pip install tkinterdnd2")

# ==========================================
# CORE CONVERTER LOGIC (Strictly WORK3 Baseline)
# ==========================================

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

def generate_comp_file(layers, psd_width, psd_height, output_dir):
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
        
        if layer["type"] == "TEXT" and layer.get("text"):
            t = layer["text"]
            text_content = str(t["content"]).replace('"', '\\"').replace("\n", "\\n")
            
            pixel_height = float(t.get("pixel_height", 50.0))
            fusion_size = (pixel_height * 1.6) / psd_height
            
            tool_def = f"""\t\t{layer_name} = TextPlus {{
\t\t\tCtrlWZoom = false,
\t\t\tInputs = {{
\t\t\t\tGlobalOut = Input {{ Value = 1000, }},
\t\t\t\tStyledText = Input {{ Value = "{text_content}", }},
\t\t\t\tFont = Input {{ Value = "Arial", }},
\t\t\t\tSize = Input {{ Value = {fusion_size:.4f}, }},
\t\t\t\tCenter = Input {{ Value = {{ 0.5, 0.5 }}, }},
\t\t\t}},
\t\t\tViewInfo = OperatorInfo {{
\t\t\t\tPos = {{ {current_x}, {Y_LOADER} }},
\t\t\t}},
\t\t}},"""
        else:
            img_filename = f"layer_{i:03d}_{sanitize_name(layer_name_raw)}.png"
            # REVERTED TO STRICT WORK3 ABSOLUTE PATHING
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
        
        tools_section.append({"name": layer_name, "def": tool_def, "id": tool_id})
        tool_id += 1
        
        transform_name = get_unique_name(f"Transform_{layer_name}", existing_names)
        existing_names.add(transform_name)
        
        bbox = layer.get("bbox", [0, 0, psd_width, psd_height])
        
        if layer["type"] == "TEXT":
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

def convert_psd_to_comp(psd_path, output_dir=None):
    if not output_dir:
        output_dir = os.path.splitext(psd_path)[0] + "_fusion"
    
    output_dir = os.path.abspath(output_dir)
    layers_dir = os.path.join(output_dir, "layers")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(layers_dir, exist_ok=True)
    
    print(f"Converting: {psd_path}")
    print(f"Output directory: {output_dir}")
    
    try:
        from psd_tools import PSDImage
        from psd_tools.api.layers import PixelLayer, ShapeLayer, SmartObjectLayer, Group, TypeLayer
        
        print("Reading PSD file (this may take a moment)...")
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
                    bbox = [float(getattr(layer, 'left', 0)), float(getattr(layer, 'top', 0)), float(getattr(layer, 'right', psd_width)), float(getattr(layer, 'bottom', psd_height))]
                    
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
                        "bbox": [float(getattr(layer, 'left', 0)), float(getattr(layer, 'top', 0)), float(getattr(layer, 'right', psd_width)), float(getattr(layer, 'bottom', psd_height))],
                        "type": "RASTER",
                        "layer_obj": layer
                    }
                    layers.append(layer_data)
        
        extract_layers(psd)
        
        print("\nExporting layer images...")
        for i, layer in enumerate(layers):
            if layer["type"] == "RASTER":
                img_filename = f"layer_{i:03d}_{sanitize_name(layer['name'])}.png"
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
        
        comp_content = generate_comp_file(layers, psd_width, psd_height, output_dir)
        comp_path = os.path.join(output_dir, "composition.comp")
        with open(comp_path, 'w', encoding='utf-8') as f:
            f.write(comp_content)
        
        print(f"\n✅ SUCCESS! Fusion File Saved to:")
        print(f"📁 {comp_path}")
        return True
        
    except ImportError:
        print("ERROR: psd-tools not installed.")
        print("Please open command prompt and run: pip install psd-tools pillow")
        return False
    except Exception as e:
        print(f"ERROR during conversion: {str(e)}")
        return False

# ==========================================
# GRAPHICAL USER INTERFACE (DARK MODE + DND)
# ==========================================

class TextRedirector(object):
    """Redirects print() statements to the GUI text box."""
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_text):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, str_text)
        self.widget.see(tk.END)
        self.widget.configure(state='disabled')

    def flush(self):
        pass

# Select the base class depending on whether tkinterdnd2 is installed
BaseTk = TkinterDnD.Tk if HAS_DND else tk.Tk

class PSDtoFusionApp(BaseTk):
    def __init__(self):
        super().__init__()
        
        self.title("PSD to DaVinci Fusion Converter")
        self.geometry("680x520")
        
        # --- DARK MODE THEME COLORS ---
        self.bg_main = "#202225"
        self.bg_frame = "#2F3136"
        self.fg_main = "#DCDDDE"
        self.accent = "#5865F2"
        self.accent_hover = "#4752C4"
        self.input_bg = "#40444B"
        
        self.configure(bg=self.bg_main, padx=20, pady=20)
        
        # --- File Selection Variables ---
        self.psd_path_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        
        self.create_widgets()
        
        # --- DRAG AND DROP SETUP ---
        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Redirect standard output to the text widget
        sys.stdout = TextRedirector(self.log_text)
        print("========================================")
        print("  🎨 PSD to Fusion Converter Ready")
        print("========================================")
        if HAS_DND:
            print("✨ Drag and Drop is ENABLED. Drop a .psd file anywhere here!")
        else:
            print("❌ Drag and Drop disabled (tkinterdnd2 missing).")
        print("\nWaiting for file...\n")

    def handle_drop(self, event):
        """Processes files dropped onto the app window."""
        file_path = event.data
        # TkinterDnD sometimes wraps paths with spaces in curly braces
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
            
        if file_path.lower().endswith('.psd'):
            self.psd_path_var.set(file_path)
            print(f"📥 Loaded PSD: {os.path.basename(file_path)}")
        else:
            messagebox.showwarning("Invalid File", "Please drop a .psd file.")

    def create_widgets(self):
        # 1. PSD File Row
        tk.Label(self, text="1. Select or Drop PSD File:", font=("Segoe UI", 11, "bold"), bg=self.bg_main, fg=self.fg_main).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        psd_frame = tk.Frame(self, bg=self.bg_main)
        psd_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        psd_frame.columnconfigure(0, weight=1)
        
        tk.Entry(psd_frame, textvariable=self.psd_path_var, width=60, font=("Segoe UI", 10), bg=self.input_bg, fg=self.fg_main, insertbackground=self.fg_main, relief="flat").grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=5)
        tk.Button(psd_frame, text="Browse", command=self.browse_psd, bg=self.bg_frame, fg=self.fg_main, activebackground=self.input_bg, activeforeground="white", relief="flat", padx=15, pady=3).grid(row=0, column=1)
        
        # 2. Output Folder Row
        tk.Label(self, text="2. Output Folder (Optional):", font=("Segoe UI", 11, "bold"), bg=self.bg_main, fg=self.fg_main).grid(row=2, column=0, sticky="w", pady=(0, 5))
        tk.Label(self, text="Leave blank to save next to the PSD file.", font=("Segoe UI", 9, "italic"), bg=self.bg_main, fg="#8E9297").grid(row=3, column=0, sticky="w", pady=(0, 5))
        
        out_frame = tk.Frame(self, bg=self.bg_main)
        out_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        out_frame.columnconfigure(0, weight=1)
        
        tk.Entry(out_frame, textvariable=self.output_dir_var, width=60, font=("Segoe UI", 10), bg=self.input_bg, fg=self.fg_main, insertbackground=self.fg_main, relief="flat").grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=5)
        tk.Button(out_frame, text="Browse", command=self.browse_output, bg=self.bg_frame, fg=self.fg_main, activebackground=self.input_bg, activeforeground="white", relief="flat", padx=15, pady=3).grid(row=0, column=1)
        
        # 3. Convert Button
        self.convert_btn = tk.Button(self, text="🚀 CONVERT TO FUSION", font=("Segoe UI", 12, "bold"), bg=self.accent, fg="white", activebackground=self.accent_hover, activeforeground="white", relief="flat", height=2, command=self.start_conversion)
        self.convert_btn.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        
        # 4. Status/Log Window
        tk.Label(self, text="Console Output:", font=("Segoe UI", 10, "bold"), bg=self.bg_main, fg="#8E9297").grid(row=6, column=0, sticky="w", pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(self, height=10, state='disabled', bg=self.bg_frame, fg=self.fg_main, font=("Consolas", 9), relief="flat")
        self.log_text.grid(row=7, column=0, sticky="nsew")
        
        self.rowconfigure(7, weight=1)
        self.columnconfigure(0, weight=1)

    def browse_psd(self):
        filepath = filedialog.askopenfilename(
            title="Select PSD File",
            filetypes=(("Photoshop Files", "*.psd"), ("All Files", "*.*"))
        )
        if filepath:
            self.psd_path_var.set(filepath)
            print(f"📥 Selected PSD: {os.path.basename(filepath)}")

    def browse_output(self):
        folderpath = filedialog.askdirectory(title="Select Output Folder")
        if folderpath:
            self.output_dir_var.set(folderpath)

    def start_conversion(self):
        psd_path = self.psd_path_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        
        if not psd_path:
            messagebox.showwarning("Missing Input", "Please select or drop a PSD file first!")
            return
            
        if not os.path.exists(psd_path):
            messagebox.showerror("Error", "The selected PSD file does not exist!")
            return
            
        if not output_dir:
            output_dir = None 
            
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
            
        self.convert_btn.config(state="disabled", text="⏳ CONVERTING... PLEASE WAIT", bg=self.bg_frame)
        
        threading.Thread(target=self.run_conversion_thread, args=(psd_path, output_dir), daemon=True).start()

    def run_conversion_thread(self, psd_path, output_dir):
        success = convert_psd_to_comp(psd_path, output_dir)
        self.after(0, self.finish_conversion, success)

    def finish_conversion(self, success):
        self.convert_btn.config(state="normal", text="🚀 CONVERT TO FUSION", bg=self.accent)
        if success:
            messagebox.showinfo("Success", "Conversion completed successfully!\nDrag the generated .comp file into DaVinci Resolve.")
        else:
            messagebox.showerror("Failed", "Conversion encountered an error. Check the console log for details.")

if __name__ == "__main__":
    app = PSDtoFusionApp()
    app.mainloop()