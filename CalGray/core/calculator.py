import numpy as np

def load_data_to_array(data, width, height):
    """将数据转换为numpy数组"""
    arr = np.zeros((height, width), dtype=np.float64)
    for x, y, gray in data:
        if 0 <= x < width and 0 <= y < height:
            arr[y, x] = gray
    return arr

def array_to_data(arr):
    """将numpy数组转换为数据列表"""
    data = []
    height, width = arr.shape
    for y in range(height):
        for x in range(width):
            data.append((x, y, int(arr[y, x])))
    return data

def calculate(data1, data2, operation, width, height):
    """对两组数据进行四则运算"""
    arr1 = load_data_to_array(data1, width, height)
    arr2 = load_data_to_array(data2, width, height)
    
    if operation == 'add':
        result = arr1 + arr2
    elif operation == 'subtract':
        result = arr1 - arr2
    elif operation == 'multiply':
        result = arr1 * arr2
    elif operation == 'divide':
        result = np.divide(arr1, arr2, out=np.zeros_like(arr1), where=arr2 != 0)
    else:
        raise ValueError("Unsupported operation")
    
    result = np.clip(result, 0, 255)
    return array_to_data(result)
