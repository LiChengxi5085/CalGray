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
