import sys
import os

import PyQt5.QtCore
qt_path = os.path.dirname(PyQt5.QtCore.__file__)
platform_plugin_path = os.path.join(qt_path, 'Qt5', 'plugins')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platform_plugin_path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QComboBox,
                             QListWidget, QLabel, QMessageBox, QSplitter,
                             QTextEdit, QTabWidget, QGroupBox, QGridLayout,
                             QLineEdit, QCheckBox, QSlider, QInputDialog)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, qRgb
from PyQt5.QtCore import Qt, pyqtSignal

from core.image_processor import image_to_grayscale_data, grayscale_data_to_image
from core.file_io import save_to_txt, load_from_txt, save_to_csv, load_from_csv, get_dimensions
from core.calculator import calculate
from core.visualizer import plot_3d, plot_2d

class LayerPreview(QLabel):
    """自定义图层预览控件，支持鼠标选择参考点"""
    reference_selected = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 2px solid #ccc;")
        self.setAlignment(Qt.AlignCenter)
        self.ref_point = None
        self.image_rect = None
    
    def set_image(self, pixmap):
        self.pixmap = pixmap
        self.setPixmap(pixmap)
        # 计算图片在标签中的实际位置
        if pixmap:
            label_width = self.width()
            label_height = self.height()
            img_width = pixmap.width()
            img_height = pixmap.height()
            
            scale = min(label_width / img_width, label_height / img_height)
            scaled_width = int(img_width * scale)
            scaled_height = int(img_height * scale)
            
            x = (label_width - scaled_width) // 2
            y = (label_height - scaled_height) // 2
            self.image_rect = (x, y, scaled_width, scaled_height)
            self.scale = scale
        else:
            self.image_rect = None
    
    def mousePressEvent(self, event):
        if self.image_rect and self.pixmap:
            x, y, w, h = self.image_rect
            mouse_x = event.x()
            mouse_y = event.y()
            
            if x <= mouse_x <= x + w and y <= mouse_y <= y + h:
                # 转换为图片坐标
                img_x = int((mouse_x - x) / self.scale)
                img_y = int((mouse_y - y) / self.scale)
                self.ref_point = (img_x, img_y)
                self.reference_selected.emit(img_x, img_y)
                self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.ref_point and self.image_rect:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2))
            x, y, w, h = self.image_rect
            dot_x = x + int(self.ref_point[0] * self.scale)
            dot_y = y + int(self.ref_point[1] * self.scale)
            
            # 绘制十字准星
            painter.drawLine(dot_x - 10, dot_y, dot_x + 10, dot_y)
            painter.drawLine(dot_x, dot_y - 10, dot_x, dot_y + 10)
            painter.drawEllipse(dot_x - 5, dot_y - 5, 10, 10)

class InteractivePreview(QLabel):
    """增强版图层预览控件，支持多图层、拖动、缩放和参考点选择"""
    reference_selected = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)
        
        # 多图层支持
        self.layers = []  # [{pixmap, offset, scale, opacity}]
        self.canvas_size = (0, 0)  # 画布大小，初始为 0
        self.selected_layer_index = -1  # 当前选中的图层索引
        
        self.scale = 1.0
        self.ref_point = None
        self.is_dragging = False
        self.last_pos = None
        
        self.setMinimumSize(500, 500)
    
    def add_layer(self, data, width, height, name=""):
        """添加一个图层"""
        if not data or width <= 0 or height <= 0:
            return None
        
        # 创建图像 - 使用 Format_RGB32 确保正确显示灰度
        img = QImage(width, height, QImage.Format_RGB32)
        
        # 填充白色背景
        img.fill(Qt.white)
        
        # 逐点设置灰度值
        for x, y, gray in data:
            if 0 <= x < width and 0 <= y < height:
                # 确保灰度值在有效范围内
                gray_val = max(0, min(255, int(gray)))
                # 使用 qRgb 创建 RGB 颜色
                img.setPixel(x, y, qRgb(gray_val, gray_val, gray_val))
        
        pixmap = QPixmap.fromImage(img)
        
        layer = {
            'pixmap': pixmap,
            'offset': [0, 0],
            'scale': 1.0,
            'opacity': 1.0,
            'name': name,
            'original_size': (width, height)
        }
        self.layers.append(layer)
        
        # 更新画布大小为所有图层的最大尺寸
        max_w = max(l['original_size'][0] for l in self.layers)
        max_h = max(l['original_size'][1] for l in self.layers)
        self.canvas_size = (max_w, max_h)
        
        self.update()
        return layer
    
    def clear_layers(self):
        """清空所有图层"""
        self.layers = []
        self.canvas_size = (0, 0)
        self.scale = 1.0
        self.selected_layer_index = -1
        self.update()
    
    def reset_view(self):
        """重置视图"""
        self.scale = 1.0
        for layer in self.layers:
            layer['offset'] = [0, 0]
            layer['scale'] = 1.0
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制画布区域（白色背景 + 边框）
        label_w = self.width()
        label_h = self.height()
        
        # 计算画布在当前缩放下的尺寸
        canvas_w = int(self.canvas_size[0] * self.scale)
        canvas_h = int(self.canvas_size[1] * self.scale)
        
        # 画布位置（居中）
        canvas_x = (label_w - canvas_w) // 2
        canvas_y = (label_h - canvas_h) // 2
        
        # 如果没有图层，显示提示信息
        if not self.layers or self.canvas_size[0] == 0:
            painter.setPen(Qt.black)
            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "双击文件列表中的文件添加图层")
            return
        
        # 绘制画布边界（红色边框表示可见区域）
        painter.setPen(QPen(Qt.red, 3))
        painter.drawRect(canvas_x, canvas_y, canvas_w, canvas_h)
        
        # 绘制画布背景
        painter.fillRect(canvas_x, canvas_y, canvas_w, canvas_h, Qt.white)
        
        # 绘制所有图层
        for i, layer in enumerate(self.layers):
            pixmap = layer['pixmap']
            if not pixmap:
                continue
            
            # 计算缩放后的图像尺寸
            orig_w = pixmap.width()
            orig_h = pixmap.height()
            layer_scale = layer['scale'] * self.scale
            scaled_w = int(orig_w * layer_scale)
            scaled_h = int(orig_h * layer_scale)
            
            # 计算绘制位置 - 从左上角开始，不再居中
            offset = layer['offset']
            # 确保坐标是整数
            draw_x = int(canvas_x + offset[0])
            draw_y = int(canvas_y + offset[1])
            
            # 应用透明度
            opacity = layer['opacity']
            if opacity < 1.0:
                painter.setOpacity(opacity)
            
            # 缩放并绘制图像
            scaled_pixmap = pixmap.scaled(
                scaled_w, scaled_h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(draw_x, draw_y, scaled_pixmap)
            
            # 绘制图层边框
            painter.setOpacity(1.0)
            if i == self.selected_layer_index:
                # 选中的图层用绿色粗边框
                painter.setPen(QPen(Qt.green, 3))
            else:
                painter.setPen(QPen(Qt.blue, 1))
            painter.drawRect(draw_x - 1, draw_y - 1, scaled_w + 2, scaled_h + 2)
            
            # 绘制图层标签
            painter.setPen(Qt.black)
            painter.drawText(draw_x + 5, draw_y + 15, f"{layer['name']} ({layer_scale*100:.0f}%)")
        
        # 绘制参考点标记
        if self.ref_point:
            ref_x = canvas_x + int(self.ref_point[0] * self.scale)
            ref_y = canvas_y + int(self.ref_point[1] * self.scale)
            
            painter.setPen(QPen(Qt.red, 2))
            painter.drawLine(ref_x - 15, ref_y, ref_x + 15, ref_y)
            painter.drawLine(ref_x, ref_y - 15, ref_x, ref_y + 15)
            painter.drawEllipse(ref_x - 6, ref_y - 6, 12, 12)
        
        # 绘制信息
        painter.setPen(Qt.black)
        painter.drawText(5, 15, f"预览缩放: {self.scale*100:.0f}%")
        painter.drawText(5, 35, f"画布尺寸: {self.canvas_size[0]}x{self.canvas_size[1]}")
        painter.drawText(5, 55, f"图层数量: {len(self.layers)}")
        painter.drawText(5, 75, "红色边框=画布边界")
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 开始拖动 - 只拖动选中的图层
            self.is_dragging = True
            self.last_pos = event.pos()
            
            # 检测点击了哪个图层
            self.selected_layer_index = self.get_layer_at(event.pos())
            self.update()
        elif event.button() == Qt.RightButton:
            # 右键取消参考点
            self.ref_point = None
            self.update()
    
    def get_layer_at(self, pos):
        """获取指定位置的图层索引"""
        label_w = self.width()
        label_h = self.height()
        
        # 计算画布位置
        canvas_w = int(self.canvas_size[0] * self.scale)
        canvas_h = int(self.canvas_size[1] * self.scale)
        canvas_x = (label_w - canvas_w) // 2
        canvas_y = (label_h - canvas_h) // 2
        
        # 从后往前检查图层（最上面的图层优先）
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            pixmap = layer['pixmap']
            if not pixmap:
                continue
            
            # 计算图层位置 - 从左上角开始
            orig_w = pixmap.width()
            orig_h = pixmap.height()
            layer_scale = layer['scale'] * self.scale
            scaled_w = int(orig_w * layer_scale)
            scaled_h = int(orig_h * layer_scale)
            
            offset = layer['offset']
            draw_x = canvas_x + offset[0]
            draw_y = canvas_y + offset[1]
            
            # 检查是否点击在这个图层范围内
            if draw_x <= pos.x() <= draw_x + scaled_w and draw_y <= pos.y() <= draw_y + scaled_h:
                return i
        
        return -1
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_dragging and self.last_pos and self.selected_layer_index >= 0:
            # 检查图层列表是否为空
            if not self.layers:
                return
            
            delta = event.pos() - self.last_pos
            
            # 将鼠标移动转换为画布坐标变化
            # delta是预览窗口中的像素变化，需要除以预览缩放得到画布坐标变化
            # 确保缩放不为零
            scale = self.scale if self.scale != 0 else 1.0
            canvas_delta_x = delta.x() / scale
            canvas_delta_y = delta.y() / scale
            
            # 只移动选中的图层（使用画布坐标）
            self.layers[self.selected_layer_index]['offset'][0] += canvas_delta_x
            self.layers[self.selected_layer_index]['offset'][1] += canvas_delta_y
            
            self.last_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.last_pos = None
        elif event.button() == Qt.MiddleButton:
            # 中键点击选择参考点
            self.select_reference_at(event.x(), event.y())
    
    def wheelEvent(self, event):
        """滚轮缩放事件"""
        angle = event.angleDelta().y()
        if angle > 0:
            self.scale *= 1.1
        else:
            self.scale /= 1.1
        
        self.scale = max(0.1, min(10.0, self.scale))
        self.update()
    
    def select_reference_at(self, mouse_x, mouse_y):
        """在指定位置选择参考点"""
        label_w = self.width()
        label_h = self.height()
        
        # 计算画布位置
        canvas_w = int(self.canvas_size[0] * self.scale)
        canvas_h = int(self.canvas_size[1] * self.scale)
        canvas_x = (label_w - canvas_w) // 2
        canvas_y = (label_h - canvas_h) // 2
        
        # 检查是否在画布范围内
        if canvas_x <= mouse_x <= canvas_x + canvas_w and canvas_y <= mouse_y <= canvas_y + canvas_h:
            # 转换为画布坐标（参考点）
            img_x = int((mouse_x - canvas_x) / self.scale)
            img_y = int((mouse_y - canvas_y) / self.scale)
            
            if 0 <= img_x < self.canvas_size[0] and 0 <= img_y < self.canvas_size[1]:
                self.ref_point = (img_x, img_y)
                self.reference_selected.emit(img_x, img_y)
                self.update()

class ImageDataConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CalGary v1.0")
        self.setGeometry(100, 100, 1200, 800)
        self.is_chinese = True
        self.init_ui()
        self.data_files = {}
        self.current_data = None
        self.current_width = 0
        self.current_height = 0
        
        self.init_ui()
    
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.tab_widget = QTabWidget()
        
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        
        self.init_tab1()
        self.init_tab2()
        self.init_tab3()
        
        self.tab_widget.addTab(self.tab1, "图片转数据")
        self.tab_widget.addTab(self.tab2, "数据运算")
        self.tab_widget.addTab(self.tab3, "数据转图片")
        
        left_layout.addWidget(self.tab_widget)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 中英文切换按钮
        self.lang_button = QPushButton("English")
        self.lang_button.clicked.connect(self.toggle_language)
        right_layout.addWidget(self.lang_button)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        
        self.data_preview = QTextEdit()
        self.data_preview.setReadOnly(True)
        self.data_preview.setMaximumHeight(150)
        
        self.label_preview = QLabel("预览:")
        self.label_data_preview = QLabel("数据预览:")
        right_layout.addWidget(self.label_preview)
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.label_data_preview)
        right_layout.addWidget(self.data_preview)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
    
    def init_tab1(self):
        layout = QVBoxLayout(self.tab1)
        
        self.image_list = QListWidget()
        
        self.btn_select = QPushButton("选择图片")
        self.btn_select.clicked.connect(self.select_images)
        
        self.btn_convert = QPushButton("转换并导出")
        self.btn_convert.clicked.connect(self.convert_and_export)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["txt", "csv"])
        
        self.label_selected_images = QLabel("已选择的图片:")
        self.label_export_format = QLabel("导出格式:")
        layout.addWidget(self.label_selected_images)
        layout.addWidget(self.image_list)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.label_export_format)
        layout.addWidget(self.format_combo)
        layout.addWidget(self.btn_convert)
    
    def init_tab2(self):
        main_layout = QHBoxLayout(self.tab2)
        
        # 左侧控制面板
        left_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.file_list.itemClicked.connect(self.on_file_clicked)
        
        self.btn_load = QPushButton("加载数据文件")
        self.btn_load.clicked.connect(self.load_data_files)
        
        self.btn_remove = QPushButton("移除选中文件")
        self.btn_remove.clicked.connect(self.remove_selected_files)
        
        self.label_files = QLabel("已加载的数据文件（双击预览，多图层叠加显示）:")
        left_layout.addWidget(self.label_files)
        left_layout.addWidget(self.file_list)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_remove)
        left_layout.addLayout(btn_layout)
        
        self.file_mapping_label = QLabel()
        self.file_mapping_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        left_layout.addWidget(self.file_mapping_label)
        
        # 每个图层的设置
        self.layer_settings_group = QGroupBox("图层设置（选中文件后可调整）")
        layer_settings_layout = QGridLayout()
        
        self.label_scale = QLabel("缩放 %:")
        layer_settings_layout.addWidget(self.label_scale, 0, 0)
        self.scale_spin = QLineEdit("100")
        self.scale_spin.setMaximumWidth(80)
        self.scale_spin.textChanged.connect(self.on_layer_setting_changed)
        layer_settings_layout.addWidget(self.scale_spin, 0, 1)
        
        self.label_opacity = QLabel("透明度 %:")
        layer_settings_layout.addWidget(self.label_opacity, 1, 0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_layer_setting_changed)
        layer_settings_layout.addWidget(self.opacity_slider, 1, 1)
        self.opacity_label = QLabel("100%")
        self.opacity_label.setMaximumWidth(50)
        layer_settings_layout.addWidget(self.opacity_label, 1, 2)
        
        self.layer_settings_group.setLayout(layer_settings_layout)
        left_layout.addWidget(self.layer_settings_group)
        
        # 图层顺序调整
        self.order_group = QGroupBox("图层顺序（选中图层后调整）")
        order_layout = QHBoxLayout()
        
        self.btn_up = QPushButton("上移")
        self.btn_up.clicked.connect(self.move_layer_up)
        order_layout.addWidget(self.btn_up)
        
        self.btn_down = QPushButton("下移")
        self.btn_down.clicked.connect(self.move_layer_down)
        order_layout.addWidget(self.btn_down)
        
        self.btn_top = QPushButton("置顶")
        self.btn_top.clicked.connect(self.move_layer_top)
        order_layout.addWidget(self.btn_top)
        
        self.btn_bottom = QPushButton("置底")
        self.btn_bottom.clicked.connect(self.move_layer_bottom)
        order_layout.addWidget(self.btn_bottom)
        
        self.order_group.setLayout(order_layout)
        left_layout.addWidget(self.order_group)
        
        # 图层预览区域
        self.layer_group = QGroupBox("图层预览（拖动移动，滚轮缩放，画布边界已标记）")
        layer_layout = QVBoxLayout()
        
        # 添加缩放控制
        scale_layout = QHBoxLayout()
        self.label_zoom = QLabel("预览缩放:")
        scale_layout.addWidget(self.label_zoom)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(50)
        scale_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("100%")
        scale_layout.addWidget(self.zoom_label)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        layer_layout.addLayout(scale_layout)
        
        self.layer_preview = InteractivePreview()
        self.layer_preview.setMinimumSize(500, 500)
        layer_layout.addWidget(self.layer_preview)
        
        # 添加重新加载预览按钮
        self.btn_refresh = QPushButton("刷新预览")
        self.btn_refresh.clicked.connect(self.refresh_preview)
        layer_layout.addWidget(self.btn_refresh)
        
        self.layer_group.setLayout(layer_layout)
        left_layout.addWidget(self.layer_group)
        
        self.label_formula = QLabel("自定义公式:")
        self.label_formula_desc = QLabel("说明：使用 A,B,C,D...代表上方列表中的文件（按顺序）")
        self.label_formula_example = QLabel("示例：(A+B)*C/2  或  A*B-C+D")
        left_layout.addWidget(self.label_formula)
        left_layout.addWidget(self.label_formula_desc)
        left_layout.addWidget(self.label_formula_example)
        
        self.formula_input = QTextEdit()
        self.formula_input.setMaximumHeight(60)
        self.formula_input.setPlaceholderText("输入公式，如：(A+B)*C/2")
        left_layout.addWidget(self.formula_input)
        
        self.btn_calculate = QPushButton("执行运算")
        self.btn_calculate.clicked.connect(self.execute_calculation)
        left_layout.addWidget(self.btn_calculate)
        
        self.btn_export = QPushButton("导出运算结果")
        self.btn_export.clicked.connect(self.export_result)
        left_layout.addWidget(self.btn_export)
        
        main_layout.addLayout(left_layout)
        
        # 右侧运算结果预览
        right_layout = QVBoxLayout()
        self.label_result_preview = QLabel("运算结果预览:")
        right_layout.addWidget(self.label_result_preview)
        self.result_preview = QLabel()
        self.result_preview.setAlignment(Qt.AlignCenter)
        self.result_preview.setStyleSheet("border: 1px solid #ccc;")
        self.result_preview.setMinimumSize(400, 400)
        right_layout.addWidget(self.result_preview)
        
        main_layout.addLayout(right_layout)
    
    def init_tab3(self):
        layout = QVBoxLayout(self.tab3)
        
        self.btn_load_data = QPushButton("加载数据文件")
        self.btn_load_data.clicked.connect(self.load_single_data)
        
        self.btn_convert_to_image = QPushButton("转换为图片")
        self.btn_convert_to_image.clicked.connect(self.convert_to_image)
        
        self.btn_plot_3d = QPushButton("生成3D图")
        self.btn_plot_3d.clicked.connect(self.plot_3d_view)
        
        self.current_file_label = QLabel("当前文件: 无")
        
        layout.addWidget(self.current_file_label)
        layout.addWidget(self.btn_load_data)
        layout.addWidget(self.btn_convert_to_image)
        layout.addWidget(self.btn_plot_3d)
    
    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.tiff *.tif)")
        for file in files:
            if file not in [self.image_list.item(i).text() for i in range(self.image_list.count())]:
                self.image_list.addItem(file)
    
    def convert_and_export(self):
        export_format = self.format_combo.currentText()
        
        if self.image_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择图片")
            return
        
        default_dir = os.path.join(os.path.expanduser("~"), "Documents")
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", default_dir)
        
        if not save_dir:
            return
        
        save_dir = save_dir.replace("/", "\\")
        
        for i in range(self.image_list.count()):
            image_path = self.image_list.item(i).text()
            try:
                data, width, height = image_to_grayscale_data(image_path)
                
                file_name = os.path.splitext(os.path.basename(image_path))[0]
                export_path = os.path.join(save_dir, f"{file_name}.{export_format}")
                export_path = export_path.replace("/", "\\")
                
                if export_format == "txt":
                    save_to_txt(data, export_path)
                else:
                    save_to_csv(data, export_path)
                
                QMessageBox.information(self, "成功", f"已导出: {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"处理 {image_path} 时出错: {str(e)}")
        
        self.image_list.clear()
    
    def load_data_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择数据文件", "", 
            "数据文件 (*.txt *.csv)")
        
        for file in files:
            if file not in self.data_files:
                try:
                    if file.endswith('.txt'):
                        data = load_from_txt(file)
                    else:
                        data = load_from_csv(file)
                    self.data_files[file] = data
                    self.file_list.addItem(file)
                    self.update_file_mapping()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"加载 {file} 时出错：{str(e)}")
    
    def update_file_mapping(self):
        """更新文件与字母的映射显示"""
        mapping_text = "文件对应关系：\n"
        for i in range(self.file_list.count()):
            letter = chr(ord('A') + i)
            file_path = self.file_list.item(i).text()
            file_name = os.path.basename(file_path)
            mapping_text += f"{letter} = {file_name}\n"
        self.file_mapping_label.setText(mapping_text)
    
    def remove_selected_files(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.text()
            if file_path in self.data_files:
                del self.data_files[file_path]
            self.file_list.takeItem(self.file_list.row(item))
        self.update_file_mapping()
        # 清空预览
        self.layer_preview.clear_layers()
    
    def on_file_double_clicked(self, item):
        """双击文件时添加到预览（图层叠加）"""
        file_path = item.text()
        data = self.data_files.get(file_path)
        if data:
            try:
                w, h = get_dimensions(data)
                name = os.path.basename(file_path)
                
                # 检查是否已存在同名图层
                for layer in self.layer_preview.layers:
                    if layer['name'] == name:
                        # 如果已存在，选中它而不是重复添加
                        self.layer_preview.selected_layer_index = self.layer_preview.layers.index(layer)
                        self.layer_preview.update()
                        return
                
                # 添加为新图层
                self.layer_preview.add_layer(data, w, h, name)
                self.current_preview_file = file_path
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加图层失败：{str(e)}")
    
    def on_file_clicked(self, item):
        """单击文件时同步选中对应的图层"""
        file_path = item.text()
        
        # 查找对应的图层索引
        for i, layer in enumerate(self.layer_preview.layers):
            if layer['name'] == os.path.basename(file_path):
                self.layer_preview.selected_layer_index = i
                
                # 更新设置控件的值
                self.scale_spin.setText(f"{int(layer['scale'] * 100)}")
                self.opacity_slider.setValue(int(layer['opacity'] * 100))
                self.opacity_label.setText(f"{int(layer['opacity'] * 100)}%")
                
                self.layer_preview.update()
                break
    
    def move_layer_up(self):
        """将选中的图层上移"""
        idx = self.layer_preview.selected_layer_index
        if idx > 0 and idx < len(self.layer_preview.layers):
            # 交换位置
            self.layer_preview.layers[idx], self.layer_preview.layers[idx-1] = \
                self.layer_preview.layers[idx-1], self.layer_preview.layers[idx]
            self.layer_preview.selected_layer_index = idx - 1
            self.layer_preview.update()
    
    def move_layer_down(self):
        """将选中的图层下移"""
        idx = self.layer_preview.selected_layer_index
        if idx >= 0 and idx < len(self.layer_preview.layers) - 1:
            # 交换位置
            self.layer_preview.layers[idx], self.layer_preview.layers[idx+1] = \
                self.layer_preview.layers[idx+1], self.layer_preview.layers[idx]
            self.layer_preview.selected_layer_index = idx + 1
            self.layer_preview.update()
    
    def move_layer_top(self):
        """将选中的图层置顶"""
        idx = self.layer_preview.selected_layer_index
        if idx >= 0 and idx < len(self.layer_preview.layers):
            # 移动到最后（最后绘制的在最上面）
            layer = self.layer_preview.layers.pop(idx)
            self.layer_preview.layers.append(layer)
            self.layer_preview.selected_layer_index = len(self.layer_preview.layers) - 1
            self.layer_preview.update()
    
    def move_layer_bottom(self):
        """将选中的图层置底"""
        idx = self.layer_preview.selected_layer_index
        if idx >= 0 and idx < len(self.layer_preview.layers):
            # 移动到最前面（最先绘制的在最下面）
            layer = self.layer_preview.layers.pop(idx)
            self.layer_preview.layers.insert(0, layer)
            self.layer_preview.selected_layer_index = 0
            self.layer_preview.update()
    
    def refresh_preview(self):
        """刷新预览"""
        self.layer_preview.clear_layers()
        # 重新添加所有图层
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            data = self.data_files.get(file_path)
            if data:
                w, h = get_dimensions(data)
                name = os.path.basename(file_path)
                self.layer_preview.add_layer(data, w, h, name)
    
    def on_layer_setting_changed(self):
        """图层设置改变"""
        # 获取当前选中的图层
        if self.layer_preview.selected_layer_index < 0:
            return
        
        layer = self.layer_preview.layers[self.layer_preview.selected_layer_index]
        
        # 更新缩放
        try:
            scale = float(self.scale_spin.text()) / 100.0
            layer['scale'] = scale
        except ValueError:
            pass
        
        # 更新透明度
        opacity = self.opacity_slider.value() / 100.0
        layer['opacity'] = opacity
        self.opacity_label.setText(f"{int(opacity*100)}%")
        
        self.layer_preview.update()
    
    def on_zoom_changed(self, value):
        """缩放滑块改变"""
        self.zoom_label.setText(f"{value}%")
        self.layer_preview.scale = value / 100.0
        self.layer_preview.update()
    
    def on_reference_selected(self, x, y):
        """参考点选择事件 - 已废弃"""
        pass
    
    def parse_formula(self, formula, file_paths):
        """解析自定义公式并计算结果"""
        import numpy as np
        from scipy import ndimage
        
        file_count = len(file_paths)
        if file_count == 0:
            raise ValueError("没有加载任何文件")
        
        # 获取所有文件的尺寸和图层信息
        layer_info = []
        for file_path in file_paths:
            w, h = get_dimensions(self.data_files[file_path])
            file_name = os.path.basename(file_path)
            
            # 获取图层设置
            scale = 1.0
            offset_x = 0
            offset_y = 0
            for layer in self.layer_preview.layers:
                if layer['name'] == file_name:
                    scale = layer['scale']
                    # 图层偏移量已经是画布坐标（拖动时已转换）
                    offset_x = int(layer['offset'][0])
                    offset_y = int(layer['offset'][1])
                    break
            
            layer_info.append({
                'file_path': file_path,
                'width': w,
                'height': h,
                'scale': scale,
                'offset_x': offset_x,
                'offset_y': offset_y
            })
        
        # 计算目标尺寸（考虑缩放和偏移）
        min_x = 0
        min_y = 0
        max_x = 0
        max_y = 0
        
        for info in layer_info:
            scaled_w = int(info['width'] * info['scale'])
            scaled_h = int(info['height'] * info['scale'])
            
            # 更新边界
            min_x = min(min_x, info['offset_x'])
            min_y = min(min_y, info['offset_y'])
            max_x = max(max_x, info['offset_x'] + scaled_w)
            max_y = max(max_y, info['offset_y'] + scaled_h)
        
        # 确保尺寸为正
        target_width = max(1, max_x - min_x)
        target_height = max(1, max_y - min_y)
        
        # 计算偏移补偿（使所有内容都在画布内）
        offset_compensate_x = -min_x
        offset_compensate_y = -min_y
        
        formula = formula.upper()
        arrays = {}
        
        # 将每个文件的数据转换为数组并应用变换
        for i, info in enumerate(layer_info):
            data = self.data_files[info['file_path']]
            w, h = info['width'], info['height']
            scale = info['scale']
            offset_x = info['offset_x'] + offset_compensate_x
            offset_y = info['offset_y'] + offset_compensate_y
            
            # 创建原始数组
            arr = np.zeros((h, w), dtype=np.float64)
            for x, y, gray in data:
                if 0 <= x < w and 0 <= y < h:
                    arr[y, x] = gray
            
            # 应用缩放
            if scale != 1.0:
                arr = ndimage.zoom(arr, (scale, scale), order=1)
            
            # 创建目标尺寸的数组并放置图像（考虑偏移）
            result_arr = np.zeros((target_height, target_width), dtype=np.float64)
            
            # 获取缩放后的尺寸
            scaled_h, scaled_w = arr.shape
            
            # 计算放置位置
            start_x = max(0, -offset_x)
            start_y = max(0, -offset_y)
            end_x = min(scaled_w, target_width - offset_x)
            end_y = min(scaled_h, target_height - offset_y)
            
            # 将图像放置到目标数组中
            target_start_x = max(0, offset_x)
            target_start_y = max(0, offset_y)
            
            if start_x < end_x and start_y < end_y:
                result_arr[target_start_y:target_start_y + (end_y - start_y),
                          target_start_x:target_start_x + (end_x - start_x)] = \
                    arr[start_y:end_y, start_x:end_x]
            
            arrays[f'array_{i}'] = result_arr
            
            # 替换公式中的变量
            var_name = chr(ord('A') + i)
            formula = formula.replace(var_name, f'arrays["array_{i}"]')
        
        try:
            result = eval(formula, {"__builtins__": {}, "np": np}, {"arrays": arrays})
        except Exception as e:
            raise ValueError(f"公式计算错误：{str(e)}")
        
        # 裁剪到 0-255 范围
        result = np.clip(result, 0, 255)
        
        # 转换回数据格式
        data = []
        h, w = result.shape
        for y in range(h):
            for x in range(w):
                data.append((x, y, int(result[y, x])))
        
        return data, w, h

    def execute_calculation(self):
        selected_items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        
        if len(selected_items) < 1:
            QMessageBox.warning(self, "警告", "请至少加载一个数据文件")
            return
        
        formula = self.formula_input.toPlainText().strip()
        if not formula:
            QMessageBox.warning(self, "警告", "请输入运算公式")
            return
        
        try:
            result_data, width, height = self.parse_formula(formula, selected_items)
            
            self.result_data = result_data
            self.result_width = width
            self.result_height = height
            
            self.update_result_preview()
            
            QMessageBox.information(self, "成功", f"运算完成！\n结果尺寸：{width}x{height}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"运算时出错：{str(e)}")
    
    def update_result_preview(self):
        if hasattr(self, 'result_data') and self.result_data:
            img = grayscale_data_to_image(self.result_data, self.result_width, self.result_height)
            q_img = QImage(img.tobytes(), self.result_width, self.result_height, 
                          QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_img)
            self.result_preview.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
    
    def export_result(self):
        if not hasattr(self, 'result_data') or not self.result_data:
            QMessageBox.warning(self, "警告", "请先执行运算")
            return
        
        # 默认保存到项目目录
        default_path = os.path.join(os.path.dirname(__file__), "result.txt")
        
        file_filter = "TXT 文件 (*.txt);;CSV 文件 (*.csv)"
        save_path, selected_filter = QFileDialog.getSaveFileName(self, "保存结果", default_path, file_filter)
        
        if save_path:
            try:
                # 确保路径存在
                save_dir = os.path.dirname(save_path)
                if save_dir and not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                if selected_filter == "TXT 文件 (*.txt)" or save_path.endswith('.txt'):
                    if not save_path.endswith('.txt'):
                        save_path += '.txt'
                    save_to_txt(self.result_data, save_path)
                else:
                    if not save_path.endswith('.csv'):
                        save_path += '.csv'
                    save_to_csv(self.result_data, save_path)
                QMessageBox.information(self, "成功", f"结果已保存：{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存结果时出错：{str(e)}")
    
    def load_single_data(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", 
            "数据文件 (*.txt *.csv)")
        
        if file:
            try:
                if file.endswith('.txt'):
                    self.current_data = load_from_txt(file)
                else:
                    self.current_data = load_from_csv(file)
                self.current_width, self.current_height = get_dimensions(self.current_data)
                self.current_file_label.setText(f"当前文件: {os.path.basename(file)}")
                
                self.update_preview()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载 {file} 时出错: {str(e)}")
    
    def update_preview(self):
        if self.current_data:
            preview_text = "\n".join([f"{x},{y},{gray}" for x, y, gray in self.current_data[:10]])
            preview_text += "\n..." if len(self.current_data) > 10 else ""
            self.data_preview.setText(preview_text)
            
            img = grayscale_data_to_image(self.current_data, self.current_width, self.current_height)
            q_img = QImage(img.tobytes(), self.current_width, self.current_height, 
                          QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
    
    def convert_to_image(self):
        if not self.current_data:
            QMessageBox.warning(self, "警告", "请先加载数据文件")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", 
            "PNG图片 (*.png);;JPEG图片 (*.jpg)")
        
        if save_path:
            try:
                img = grayscale_data_to_image(self.current_data, self.current_width, self.current_height)
                img.save(save_path)
                QMessageBox.information(self, "成功", f"图片已保存: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存图片时出错: {str(e)}")
    
    def plot_3d_view(self):
        if not self.current_data:
            QMessageBox.warning(self, "警告", "请先加载数据文件")
            return
        
        # 选择分辨率
        resolution, ok = QInputDialog.getInt(self, "3D图分辨率", "请输入分辨率倍数（1-10）:", value=2, min=1, max=10)
        if not ok:
            return
        
        try:
            fig = plot_3d(self.current_data, self.current_width, self.current_height, resolution=resolution)
            fig.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成3D图时出错: {str(e)}")
    
    def toggle_language(self):
        """切换中英文界面"""
        self.is_chinese = not self.is_chinese
        
        if self.is_chinese:
            # 切换到中文
            self.setWindowTitle("CalGary v1.0")
            self.lang_button.setText("English")
            self.tab_widget.setTabText(0, "图片转数据")
            self.tab_widget.setTabText(1, "数据运算")
            self.tab_widget.setTabText(2, "数据转图片")
            
            # 主面板控件
            self.label_preview.setText("预览:")
            self.label_data_preview.setText("数据预览:")
            
            # Tab1 控件
            self.label_selected_images.setText("已选择的图片:")
            self.btn_select.setText("选择图片")
            self.label_export_format.setText("导出格式:")
            self.btn_convert.setText("转换并导出")
            
            # Tab2 控件
            self.btn_load.setText("加载数据文件")
            self.btn_remove.setText("移除选中文件")
            self.label_files.setText("已加载的数据文件（双击预览，多图层叠加显示）:")
            self.layer_settings_group.setTitle("图层设置（选中文件后可调整）")
            self.label_scale.setText("缩放 %:")
            self.label_opacity.setText("透明度 %:")
            self.order_group.setTitle("图层顺序（选中图层后调整）")
            self.btn_up.setText("上移")
            self.btn_down.setText("下移")
            self.btn_top.setText("置顶")
            self.btn_bottom.setText("置底")
            self.layer_group.setTitle("图层预览（拖动移动，滚轮缩放，画布边界已标记）")
            self.label_zoom.setText("预览缩放:")
            self.btn_refresh.setText("刷新预览")
            self.label_formula.setText("自定义公式:")
            self.label_formula_desc.setText("说明：使用 A,B,C,D...代表上方列表中的文件（按顺序）")
            self.label_formula_example.setText("示例：(A+B)*C/2  或  A*B-C+D")
            self.formula_input.setPlaceholderText("输入公式，如：(A+B)*C/2")
            self.btn_calculate.setText("执行运算")
            self.btn_export.setText("导出运算结果")
            self.label_result_preview.setText("运算结果预览:")
            
            # Tab3 控件
            self.current_file_label.setText("当前文件: 无")
            self.btn_load_data.setText("加载数据文件")
            self.btn_convert_to_image.setText("转换为图片")
            self.btn_plot_3d.setText("生成3D图")
        else:
            # 切换到英文
            self.setWindowTitle("CalGary v1.0")
            self.lang_button.setText("中文")
            self.tab_widget.setTabText(0, "Image to Data")
            self.tab_widget.setTabText(1, "Data Operation")
            self.tab_widget.setTabText(2, "Data to Image")
            
            # 主面板控件
            self.label_preview.setText("Preview:")
            self.label_data_preview.setText("Data Preview:")
            
            # Tab1 控件
            self.label_selected_images.setText("Selected Images:")
            self.btn_select.setText("Select Images")
            self.label_export_format.setText("Export Format:")
            self.btn_convert.setText("Convert & Export")
            
            # Tab2 控件
            self.btn_load.setText("Load Data Files")
            self.btn_remove.setText("Remove Selected")
            self.label_files.setText("Loaded data files (double-click to preview, multi-layer display):")
            self.layer_settings_group.setTitle("Layer Settings (adjust after selecting)")
            self.label_scale.setText("Scale %:")
            self.label_opacity.setText("Opacity %:")
            self.order_group.setTitle("Layer Order (adjust after selecting)")
            self.btn_up.setText("Move Up")
            self.btn_down.setText("Move Down")
            self.btn_top.setText("Bring to Front")
            self.btn_bottom.setText("Send to Back")
            self.layer_group.setTitle("Layer Preview (drag to move, scroll to zoom, canvas boundary marked)")
            self.label_zoom.setText("Preview Zoom:")
            self.btn_refresh.setText("Refresh Preview")
            self.label_formula.setText("Custom Formula:")
            self.label_formula_desc.setText("Note: Use A,B,C,D... to represent files in the list above (in order)")
            self.label_formula_example.setText("Example: (A+B)*C/2  or  A*B-C+D")
            self.formula_input.setPlaceholderText("Enter formula, e.g.: (A+B)*C/2")
            self.btn_calculate.setText("Execute Calculation")
            self.btn_export.setText("Export Result")
            self.label_result_preview.setText("Result Preview:")
            
            # Tab3 控件
            self.current_file_label.setText("Current File: None")
            self.btn_load_data.setText("Load Data File")
            self.btn_convert_to_image.setText("Convert to Image")
            self.btn_plot_3d.setText("Generate 3D Plot")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageDataConverter()
    window.show()
    sys.exit(app.exec_())
