import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from scipy import ndimage

def plot_3d(data, width, height, resolution=1):
    """创建3D灰度图
    
    Args:
        data: 灰度数据点列表
        width: 原始宽度
        height: 原始高度
        resolution: 分辨率倍数，默认为1，大于1时会插值放大
    """
    arr = np.zeros((height, width))
    for x, y, gray in data:
        if 0 <= x < width and 0 <= y < height:
            arr[y, x] = gray
    
    # 如果分辨率大于1，则进行插值放大
    if resolution > 1:
        arr = ndimage.zoom(arr, resolution, order=1)
        width = int(width * resolution)
        height = int(height * resolution)
    
    # 采样降低数据量，避免卡死
    step = max(1, int(min(width, height) / 100))
    arr = arr[::step, ::step]
    height_sampled, width_sampled = arr.shape
    
    x = np.arange(width_sampled) * step
    y = np.arange(height_sampled) * step
    X, Y = np.meshgrid(x, y)
    
    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    
    # 使用较低的rstride和cstride提高性能
    ax.plot_surface(X, Y, arr, cmap='gray', edgecolor='none', 
                   rstride=2, cstride=2, antialiased=False)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Gray Value')
    ax.set_title('3D Grayscale Visualization')
    
    # 调整视角
    ax.view_init(elev=35, azim=45)
    
    return fig

def plot_2d(data, width, height):
    """创建2D灰度图"""
    arr = np.zeros((height, width))
    for x, y, gray in data:
        if 0 <= x < width and 0 <= y < height:
            arr[y, x] = gray
    
    fig = plt.figure()
    plt.imshow(arr, cmap='gray', origin='upper')
    plt.colorbar(label='Gray Value')
    plt.title('2D Grayscale Image')
    plt.xlabel('X')
    plt.ylabel('Y')
    
    return fig
