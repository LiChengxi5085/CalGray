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

# CalGary - 图片灰度数据转换器

一个基于 Python + PyQt5 的 Windows 桌面程序，用于图片与灰度坐标数据之间的相互转换、多组数据的四则运算，以及 2D/3D 可视化。

## 功能特性

1. **图片 → 数据**：将 PNG、JPG、TIFF 等格式图片转换为 `x, y, gray` 坐标数据，导出为 txt 或 csv 文件。图片的透明通道（RGBA/LA/P with transparency）会被合成到白色背景上再计算。

2. **数据运算**：对两个数据文件进行像素级四则运算（加、减、乘、除），生成新的数据文件。结果自动裁剪到 `0-255` 灰度范围，除法运算自动避免除零错误。

3. **数据 → 图片**：将 txt 或 csv 数据文件还原为灰度图片，并支持 2D 热力图和 3D 曲面可视化。

## 技术栈

- **GUI**：PyQt5
- **数值计算**：NumPy, SciPy（3D 插值）
- **图像处理**：Pillow (PIL)
- **可视化**：Matplotlib（Qt5Agg 后端）
- **文件 IO**：标准库 csv + openpyxl

## 项目结构

```
calgray/
├── main.py               # 主程序入口（PyQt5 主窗口，自动设置 Qt 插件路径）
├── start.py              # Python 启动器（切换工作目录后调用 main.py）
├── CalGary.bat           # Windows 批处理启动脚本
├── requirements.txt      # 依赖列表
├── core/
│   ├── image_processor.py # 图片 ↔ 灰度坐标数据转换
│   ├── file_io.py         # txt / csv 文件读写
│   ├── calculator.py      # 四则运算（NumPy 数组）
│   └── visualizer.py      # 2D / 3D 可视化（Matplotlib）
└── dist/
    └── CalGary_Portable/  # 打包后的便携版
```

## 环境要求

- Python 3.x（开发环境使用 3.13）
- Windows 系统（推荐）

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖清单：`PyQt5`, `numpy`, `scipy`, `matplotlib`, `pillow`, `openpyxl`

## 运行程序

项目中 `main.py` 已自动设置 `QT_QPA_PLATFORM_PLUGIN_PATH` 环境变量，无需手动配置。

### 方式一：使用批处理脚本（推荐）

直接双击 `CalGary.bat`。

### 方式二：使用 Python 启动器

```bash
python start.py
```

### 方式三：直接运行

```bash
python main.py
```

## 使用说明

### 图片转数据

1. 切换到 **"图片转数据"** 标签页
2. 点击 **"选择图片"**，可选择一个或多个图片文件（PNG、JPG、TIFF 等）
3. 选择导出格式（**txt** 或 **csv**）
4. 点击 **"转换并导出"**，选择保存位置

### 数据运算

1. 切换到 **"数据运算"** 标签页
2. 点击 **"加载数据文件"**，选择两个数据文件（txt/csv）
3. 选择运算类型（**加、减、乘、除**）
4. 点击 **"执行运算"**，保存结果文件

> 注：两个数据文件需具有相同的图片尺寸（相同的 width/height），否则像素运算可能产生错位。

### 数据转图片

1. 切换到 **"数据转图片"** 标签页
2. 点击 **"加载数据文件"**，选择 txt 或 csv 文件
3. 点击 **"转换为图片"**，保存为 PNG 或 JPG 格式
4. 点击 **"生成 3D 图"**，查看以灰度值为高度的三维曲面图

## 数据格式

导出的 txt / csv 文件格式如下（带表头 `x,y,gray`）：

```
x,y,gray
0,0,128
1,0,130
2,0,145
...
```

- `x`：像素横坐标（列号，从 0 起）
- `y`：像素纵坐标（行号，从 0 起）
- `gray`：灰度值（范围 `0-255`）

文件使用 UTF-8 编码，每行一个像素点。

## 许可协议

个人学习与研究用途。
