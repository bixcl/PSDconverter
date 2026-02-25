#!/usr/bin/env python3
"""
PSD TO FUSION CONVERTER v8.2 - TEXT RASTERIZATION OPTION
Added: --rasterize-text flag to export text as PNG instead of TextPlus nodes
"""

import os
import re
import sys
import argparse  # NEW: For proper argument parsing
from PIL import Image

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

# MODIFIED: Added rasterize_text parameter
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
    
    # --- CLEAN LAYOUT SYSTEM ---
    Y_LOADER = 150
    Y_TRANSFORM = 75
    Y_MERGE = 0
    X_SPACING = 200

    # 1. CREATE MASTER CANVAS BACKGROUND
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
        
        # 2. CREATE LOADER OR TEXT NODE (Top Row)
        # MODIFIED: Check if we should rasterize text
        if is_text_layer and not rasterize_text and layer.get("text"):
            # EDITABLE TEXT PATH: Create TextPlus node
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
            # RASTERIZED PATH: Create Loader for PNG (used for both raster layers AND rasterized text)
            # For text layers being rasterized, we still need to export them as images
            if is_text_layer:
                # Text layer being rasterized - use special naming
                img_filename = f"layer_{i:03d}_{sanitize_name(layer_name_raw)}_text.png"
            else:
                # Regular raster layer
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
            # Mark that this layer needs image export (for text rasterization)
            if is_text_layer:
                layer["needs_export"] = True
        
        tools_section.append({"name": layer_name, "def": tool_def, "id": tool_id})
        tool_id += 1
        
        # 3. CREATE TRANSFORM NODE (Middle Row)
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
        
        # 4. CREATE MERGE NODE (Bottom Row)
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
    
    # 5. CREATE MEDIA OUT (End of the line)
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

# MODIFIED: Added rasterize_text parameter
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
            if not layer.get("visible", True):
                continue
                
            should_export = False
            img_filename = None
            
            if layer["type"] == "RASTER":
                # Always export raster layers
                should_export = True
                img_filename = f"layer_{i:03d}_{sanitize_name(layer['name'])}.png"
            elif layer["type"] == "TEXT" and rasterize_text:
                # Export text layers only if rasterize mode is on
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
                        # For text layers, we need to composite them from the PSD
                        # Since we don't have layer_obj for text, we need to handle this differently
                        # Actually, psd-tools TypeLayer has composite() method too
                        from psd_tools.api.layers import TypeLayer
                        # Re-find this layer in the PSD to get the object
                        for psd_layer in psd.descendants():
                            if isinstance(psd_layer, TypeLayer) and psd_layer.name == layer["name"]:
                                if export_layer_image(psd_layer, img_path, psd_width, psd_height):
                                    print(f"  ✓ Text (rasterized) -> {img_filename}")
                                break
        
        # MODIFIED: Pass rasterize_text to generator
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

if __name__ == "__main__":
    # NEW: Proper argument parsing with argparse
    parser = argparse.ArgumentParser(
        description="Convert PSD to DaVinci Fusion .comp file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python psd_to_fusion.py input.psd                    # Editable text (default)
  python psd_to_fusion.py input.psd -r                 # Rasterize text to PNG
  python psd_to_fusion.py input.psd -o output_folder   # Custom output folder
        """
    )
    
    parser.add_argument("input", help="Path to input PSD file")
    parser.add_argument("-o", "--output", help="Output directory (default: input_fusion/)")
    parser.add_argument("-r", "--rasterize-text", action="store_true", 
                        help="Rasterize text layers to PNG instead of creating editable TextPlus nodes")
    
    args = parser.parse_args()
    
    convert_psd_to_comp(args.input, args.output, args.rasterize_text)