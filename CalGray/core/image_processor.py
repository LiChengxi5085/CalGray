import numpy as np
from PIL import Image

def image_to_grayscale_data(image_path):
    """将图片转换为 x-y-灰度坐标数据"""
    img = Image.open(image_path)
    
    # 处理透明通道：如果有 alpha 通道，先转换为 RGBA，再用白色背景合成
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        # 创建白色背景
        background = Image.new('RGB', img.size, (255, 255, 255))
        
        # 如果图像不是 RGBA，先转换
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 使用 alpha 通道合成到白色背景
        background.paste(img, mask=img.split()[3])  # 3 是 alpha 通道
        img = background
    
    # 转换为灰度
    img = img.convert('L')
    img_array = np.array(img)
    
    data = []
    height, width = img_array.shape
    
    for y in range(height):
        for x in range(width):
            gray_value = img_array[y, x]
            data.append((x, y, gray_value))
    
    return data, width, height

def grayscale_data_to_image(data, width, height):
    """将灰度数据转换为图片"""
    img_array = np.zeros((height, width), dtype=np.uint8)
    
    for x, y, gray_value in data:
        if 0 <= x < width and 0 <= y < height:
            img_array[y, x] = gray_value
    
    img = Image.fromarray(img_array, mode='L')
    return img
