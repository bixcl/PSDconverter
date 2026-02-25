# PSD to DaVinci Fusion Converter (v10.1)

A professional desktop utility to convert Adobe Photoshop (PSD) files into native DaVinci Resolve Fusion Composition (.comp) files. 

## ✨ Features
- **Dark Mode UI:** Sleek, modern interface.
- **Drag & Drop:** Drop a `.psd` file anywhere to load it instantly.
- **Editable Text:** Converts PSD text to native Fusion `TextPlus` nodes.
- **Reliable Paths:** Uses absolute path mapping to ensure images never go "offline."
- **Automatic Image Extraction:** Extracts all layers to a `layers/` subfolder.

## 🚀 How to Use (EXE Version)
1. Launch `psdConverter.exe`.
2. Drag and drop your `.psd` file into the app.
3. Click **🚀 CONVERT TO FUSION**.
4. Inside DaVinci Resolve (Fusion Page), go to **File > Import > Fusion Composition** and select your new file.
5. **Important:** Click the `MediaOut1` node and press `2` on your keyboard to see the result.

## 🛠️ Development Setup
If running from source, install dependencies:
```bash
pip install psd-tools pillow tkinterdnd2 pyinstaller

python -m PyInstaller --noconsole --onefile --icon=icon.ico --collect-data tkinterdnd2 psdConverter.py