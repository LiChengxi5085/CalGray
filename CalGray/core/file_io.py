import csv

def save_to_txt(data, file_path):
    """保存数据到txt文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("x,y,gray\n")
        for row in data:
            f.write(f"{row[0]},{row[1]},{row[2]}\n")

def load_from_txt(file_path):
    """从txt文件加载数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip():
                parts = line.strip().split(',')
                data.append((int(parts[0]), int(parts[1]), int(parts[2])))
    return data

def save_to_csv(data, file_path):
    """保存数据到csv文件"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'gray'])
        for row in data:
            writer.writerow(row)

def load_from_csv(file_path):
    """从csv文件加载数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                data.append((int(row[0]), int(row[1]), int(row[2])))
    return data

def get_dimensions(data):
    """从数据中获取图片尺寸"""
    if not data:
        return 0, 0
    max_x = max(p[0] for p in data)
    max_y = max(p[1] for p in data)
    return max_x + 1, max_y + 1
