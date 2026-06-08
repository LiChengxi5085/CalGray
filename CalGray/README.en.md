# CalGary - Image Grayscale Data Converter

A Python + PyQt5 based Windows desktop application for bidirectional conversion between images and grayscale coordinate data, pixel-level arithmetic operations on multiple datasets, and 2D/3D visualization.

## Features

1. **Image → Data**: Converts PNG, JPG, TIFF and other image formats into `x, y, gray` coordinate data, exported as txt or csv files. Images with alpha channels (RGBA / LA / P with transparency) are composited onto a white background before grayscale conversion.

2. **Data Arithmetic**: Performs pixel-level four-basic arithmetic operations (add, subtract, multiply, divide) on two data files, producing a new data file. Results are automatically clipped to the `0–255` grayscale range, and division guards against division-by-zero.

3. **Data → Image**: Restores txt/csv data files back to grayscale images, with support for 2D heatmap and 3D surface visualization.

## Tech Stack

- **GUI**: PyQt5
- **Numerics**: NumPy, SciPy (3D interpolation)
- **Image Processing**: Pillow (PIL)
- **Visualization**: Matplotlib (Qt5Agg backend)
- **File IO**: Standard library `csv` + `openpyxl`

## Project Structure

```
calgray/
├── main.py               # Application entry point (PyQt5 main window, auto-sets Qt plugin path)
├── start.py              # Python launcher (changes CWD then calls main.py)
├── CalGary.bat           # Windows batch launcher
├── requirements.txt      # Dependency list
├── core/
│   ├── image_processor.py # Image ↔ grayscale coordinate data conversion
│   ├── file_io.py         # txt / csv file I/O
│   ├── calculator.py      # Arithmetic operations (NumPy arrays)
│   └── visualizer.py      # 2D / 3D visualization (Matplotlib)
└── dist/
    └── CalGary_Portable/  # Portable build output
```

## Requirements

- Python 3.x (developed on 3.13)
- Windows (recommended)

## Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `PyQt5`, `numpy`, `scipy`, `matplotlib`, `pillow`, `openpyxl`

## Running the Application

`main.py` auto-configures the `QT_QPA_PLATFORM_PLUGIN_PATH` environment variable — no manual setup is required.

### Option 1: Batch script (recommended)

Double-click `CalGary.bat`.

### Option 2: Python launcher

```bash
python start.py
```

### Option 3: Run directly

```bash
python main.py
```

## Usage Guide

### Image to Data

1. Switch to the **"Image → Data"** tab.
2. Click **"Select Image(s)"** — one or more files (PNG, JPG, TIFF, etc.).
3. Choose the export format (**txt** or **csv**).
4. Click **"Convert & Export"**, then pick a save location.

### Data Arithmetic

1. Switch to the **"Data Arithmetic"** tab.
2. Click **"Load Data File"** and select two data files (txt/csv).
3. Choose an operation (**add, subtract, multiply, divide**).
4. Click **"Execute"** and save the result.

> Note: Both data files must share the same image dimensions (same width/height), otherwise pixel-level operations may produce misaligned results.

### Data to Image

1. Switch to the **"Data → Image"** tab.
2. Click **"Load Data File"** and select a txt or csv file.
3. Click **"Convert to Image"** to save as PNG or JPG.
4. Click **"Generate 3D Plot"** to view a 3D surface chart where the Z-axis represents the grayscale value.

## Data Format

Exported txt / csv files use the following format (with a `x,y,gray` header):

```
x,y,gray
0,0,128
1,0,130
2,0,145
...
```

- `x`: pixel column index (starting from 0)
- `y`: pixel row index (starting from 0)
- `gray`: grayscale value (range `0–255`)

Files are UTF-8 encoded, one pixel per line.

## License

For personal learning and research use.
