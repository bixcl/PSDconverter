# PSD to Fusion Converter

A Python tool that converts Adobe Photoshop (.psd) files into DaVinci Resolve Fusion compositions (.comp). Available in both **Command Line Interface (CLI)** and **Dark Mode GUI** versions.

![Version](https://img.shields.io/badge/version-9.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## Features

- 🎨 **Layer Preservation**: Converts PSD layers into Fusion nodes with proper positioning
- 📝 **Text Handling**: Choose between editable TextPlus nodes or rasterized PNG images
- 🖼️ **Blend Modes**: Supports Normal, Multiply, Screen, Overlay, Soft Light, and Hard Light
- 📂 **Group Support**: Flattens Photoshop groups into merged images
- 🎯 **Opacity & Position**: Preserves layer opacity and bounding box coordinates
- 🖥️ **Modern GUI**: Dark mode interface with real-time conversion log
- ⚡ **CLI Support**: Batch processing and automation friendly

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Required Packages

```bash
pip install psd-tools pillow

================================================================================
PSD TO FUSION CONVERTER v9.1 - ALL-IN-ONE VERSION
================================================================================

A Python tool that converts Adobe Photoshop (.psd) files into DaVinci Resolve 
Fusion compositions (.comp). 

FEATURES:
- Layer Preservation: Converts PSD layers into Fusion nodes with proper positioning
- Text Handling: Choose between editable TextPlus nodes or rasterized PNG images
- Blend Modes: Supports Normal, Multiply, Screen, Overlay, Soft Light, Hard Light
- Group Support: Flattens Photoshop groups into merged images
- Opacity & Position: Preserves layer opacity and bounding box coordinates
- Modern GUI: Dark mode interface with real-time conversion log
- CLI Support: Batch processing and automation friendly

INSTALLATION:
    pip install psd-tools pillow

USAGE - GUI MODE:
    python psd_to_fusion.py
    
    Launches dark mode GUI with:
    - Click to select PSD file
    - Choose output directory  
    - Toggle "Rasterize text layers" checkbox
    - Real-time conversion log

USAGE - CLI MODE:
    python psd_to_fusion.py input.psd
    python psd_to_fusion.py input.psd -r                    # Rasterize text
    python psd_to_fusion.py input.psd -o ./output_folder    # Custom output
    python psd_to_fusion.py input.psd -r -o ./output        # Combined

ARGUMENTS:
    input               Path to input PSD file (optional, launches GUI if omitted)
    -o, --output        Output directory (default: input_fusion/)
    -r, --rasterize-text    Export text as PNG instead of editable TextPlus
    --cli               Force CLI mode even if GUI is available

TEXT HANDLING MODES:

Editable Text (Default):
    - Creates TextPlus nodes in Fusion
    - Text content can be modified in DaVinci Resolve
    - Font size approximated based on PSD text height
    - May not perfectly match complex Photoshop styling

Rasterized Text (-r flag):
    - Exports text layers as PNG images
    - Pixel-perfect preservation of Photoshop appearance
    - Not editable in Fusion (treated as image)

OUTPUT STRUCTURE:
    input_fusion/
    ├── composition.comp          # Main Fusion composition file
    └── layers/
        ├── layer_000_background.png
        ├── layer_001_logo.png
        └── ...

FUSION NODE STRUCTURE:
    MediaOut1
        ↑
    Merge_n (Final merge)
        ↑
    [Previous merges...]
        ↑
    Merge_1
        ↑
    Transform_1 ← Loader_1 / TextPlus_1
        ↑
    MasterCanvas (Background)

SUPPORTED LAYERS:
    Pixel Layer     → Loader (raster export)
    Shape Layer     → Loader (converted to raster)
    Smart Object    → Loader (rasterized)
    Text Layer      → TextPlus or Loader (depends on rasterize setting)
    Group           → Flattened Image (merged PNG)
    Hidden Layers   → Skipped (not included)

TROUBLESHOOTING:

"psd-tools not installed":
    pip install psd-tools pillow

Text layers not appearing:
    - Check layer visibility in Photoshop
    - Try rasterizing with -r flag for font compatibility

Images black/transparent:
    - Ensure layer has pixel content (not just adjustment layers)
    - Check layer visibility in PSD

Wrong layer order:
    - Processed bottom to top (PSD order)
    - First PSD layer becomes bottom Fusion layer

BUILDING EXECUTABLE:
    pyinstaller --onefile --windowed psd_to_fusion.py

VERSION HISTORY:
    v9.1 - Fixed GUI drag-and-drop compatibility
    v9.0 - Added dark mode GUI with threading
    v8.2 - Added text rasterization option
    v8.1 - Clean node layout and visibility fixes
    v8.0 - Initial release

LICENSE: MIT License - Free for personal and commercial use

DEPENDENCIES:
    psd-tools    - Adobe Photoshop file parsing
    Pillow       - Image processing and export
    tkinter      - GUI framework (included with Python)

LIMITATIONS:
    - Does not support Photoshop layer effects (shadows, glows, etc.)
    - Text styling may not transfer to TextPlus nodes
    - Adjustment layers are ignored
    - Layer masks applied on export but not editable in Fusion
