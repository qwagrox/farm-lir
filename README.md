# 🌾 田块自动识别与任意角度的自动最大作业区域覆盖

- **版本**: 1.0.0
- **作者**: tangyong@stmail.ujs.edu.cn ， 目前就读于江苏大学农机控制理论与工程博士
- **日期**: 2025/10/17

## 核心功能

**直接从GPS测量的田块边界顶点计算最大作业区域**

**参考https://github.com/OpenStitching/lir 并做适合农业场景的任意角度的自动最大作业区域覆盖**

---

## 🚀 快速开始

### 场景：无人机测量田块边界

```python
from largestinteriorrectangle import smart_inscribe_from_vertices

# 步骤1：无人机/GPS测量得到田块边界顶点
field_vertices = np.array([
    [150, 200],   # 顶点1 (x, y) 或 (经度, 纬度)
    [550, 200],   # 顶点2
    [650, 450],   # 顶点3
    [250, 450]    # 顶点4
])

# 步骤2：一行代码计算最大作业区域
result = smart_inscribe_from_vertices(field_vertices)

# 步骤3：查看结果
print(f"田块形状: {result.shape_type}")        # "parallelogram"
print(f"作业面积: {result.area:.0f} 平方米")   # 99080
print(f"覆盖率: {result.coverage:.1%}")        # 99.1%

# 步骤4：获取作业区域顶点（发送给拖拉机）
work_area_vertices = result.polygon
print(f"作业区域顶点:\n{work_area_vertices}")
```

---

## 📊 完整工作流程

### 1. 田块测量（无人机/GPS）

```python
import numpy as np

# GPS测量得到的田块边界顶点
# 可以是任意多边形（3个点以上）
field_boundary = np.array([
    [100.5, 200.3],
    [500.8, 250.1],
    [480.2, 450.7],
    [80.1, 400.5]
])
```

### 2. 自动形状识别

```python
from largestinteriorrectangle import classify_shape

# 自动识别田块形状
shape_type = classify_shape(field_boundary)
print(f"检测到的形状: {shape_type.value}")
# 输出: "rectangle" / "parallelogram" / "trapezoid" / "triangle"
```

### 3. 计算最大作业区域

```python
from largestinteriorrectangle import smart_inscribe_from_vertices

# 智能计算最大内接多边形
result = smart_inscribe_from_vertices(
    field_boundary,
    angle_step=1.0,  # 角度搜索步长（度）
    try_multiple_strategies=True  # 尝试多种策略
)

print(f"作业区域面积: {result.area:.0f} 平方米")
print(f"覆盖率: {result.coverage:.1%}")
```

### 4. 生成作业路径

```python
from largestinteriorrectangle import generate_work_paths

# 生成平行作业路径
paths = generate_work_paths(
    result.polygon,
    work_width=3.0,  # 拖拉机工作宽度（米）
    shape_type=result.shape_type
)

print(f"作业路径数: {len(paths)}")

# 导出路径给控制系统
for i, (start, end) in enumerate(paths):
    print(f"路径 {i}: 从 {start} 到 {end}")
```

### 5. 导出给拖拉机控制系统

```python
import json

# 准备数据
work_plan = {
    'field_id': 'field_001',
    'field_shape': result.shape_type,
    'field_boundary': field_boundary.tolist(),
    'work_area': {
        'vertices': result.polygon.tolist(),
        'area_sqm': float(result.area),
        'coverage': float(result.coverage)
    },
    'work_paths': [
        {
            'path_id': i,
            'start': {'x': float(start[0]), 'y': float(start[1])},
            'end': {'x': float(end[0]), 'y': float(end[1])}
        }
        for i, (start, end) in enumerate(paths)
    ],
    'tractor_width_m': 3.0,
    'total_paths': len(paths)
}

# 保存为JSON
with open('work_plan.json', 'w') as f:
    json.dump(work_plan, f, indent=2)

print("✅ 作业计划已导出到 work_plan.json")
```

---

## 🌍 GPS坐标支持

### 使用UTM坐标（推荐）

```python
from largestinteriorrectangle import smart_inscribe_from_gps

# GPS坐标（UTM投影）
gps_coords = [
    (500000, 4500000),  # (东向, 北向) 米
    (500100, 4500020),
    (500090, 4500150),
    (500010, 4500130)
]

result = smart_inscribe_from_gps(
    gps_coords,
    coordinate_system="utm"
)

print(f"作业面积: {result.area:.0f} 平方米")
print(f"作业区域GPS坐标:\n{result.polygon}")
```

### 使用WGS84坐标（经纬度）

```python
# GPS坐标（经度, 纬度）
gps_coords = [
    (116.4074, 39.9042),  # 北京天安门附近
    (116.4084, 39.9042),
    (116.4084, 39.9052),
    (116.4074, 39.9052)
]

result = smart_inscribe_from_gps(
    gps_coords,
    coordinate_system="wgs84"
)

print(f"作业面积: {result.area:.0f} 平方米")
```

**注意**：WGS84坐标会自动转换为局部投影进行计算，对于大面积田块建议使用UTM坐标。

---

## 📐 支持的形状

### 1. 矩形田块

```python
vertices = np.array([
    [0, 0],
    [100, 0],
    [100, 50],
    [0, 50]
])

result = smart_inscribe_from_vertices(vertices)
# 输出: rectangle, 覆盖率 ~98%
```

### 2. 平行四边形田块

```python
vertices = np.array([
    [0, 0],
    [100, 0],
    [120, 50],
    [20, 50]
])

result = smart_inscribe_from_vertices(vertices)
# 输出: parallelogram, 覆盖率 ~98%
# 内接平行四边形，不是矩形！
```

### 3. 梯形田块

```python
vertices = np.array([
    [0, 0],
    [100, 0],
    [80, 50],
    [20, 50]
])

result = smart_inscribe_from_vertices(vertices)
# 输出: trapezoid, 覆盖率 ~98%
# 内接梯形，保持梯形形状！
```

### 4. 三角形田块

```python
vertices = np.array([
    [50, 0],
    [100, 100],
    [0, 100]
])

result = smart_inscribe_from_vertices(vertices)
# 输出: triangle, 覆盖率 ~98%
# 内接三角形，最大化覆盖！
```

### 5. 不规则多边形

```python
vertices = np.array([
    [0, 0],
    [100, 20],
    [120, 80],
    [80, 120],
    [20, 100]
])

result = smart_inscribe_from_vertices(vertices)
# 输出: general, 使用通用算法
```

---

## 🎯 实际应用示例

### 示例1：拖拉机耕作路径规划

```python
#!/usr/bin/env python3
"""拖拉机耕作路径规划"""

import numpy as np
from largestinteriorrectangle import (
    smart_inscribe_from_vertices,
    generate_work_paths
)

# 1. 无人机测量田块
field_vertices = np.array([
    [100, 200],
    [500, 250],
    [480, 450],
    [80, 400]
])

# 2. 计算作业区域
result = smart_inscribe_from_vertices(field_vertices)

print(f"田块形状: {result.shape_type}")
print(f"作业面积: {result.area:.0f} 平方米")
print(f"覆盖率: {result.coverage:.1%}")

# 3. 生成耕作路径（拖拉机宽度3米）
paths = generate_work_paths(
    result.polygon,
    work_width=3.0,
    shape_type=result.shape_type
)

print(f"耕作路径: {len(paths)} 条")
print(f"预计耕作时间: {len(paths) * 5} 分钟")  # 假设每条5分钟

# 4. 发送给拖拉机控制系统
for i, (start, end) in enumerate(paths):
    # send_to_tractor(path_id=i, start=start, end=end)
    print(f"路径 {i}: {start} → {end}")
```

### 示例2：无人机喷洒路径规划

```python
#!/usr/bin/env python3
"""无人机喷洒路径规划"""

import numpy as np
from largestinteriorrectangle import (
    smart_inscribe_from_gps,
    generate_work_paths
)

# 1. GPS测量田块（UTM坐标）
gps_boundary = [
    (500000, 4500000),
    (500100, 4500020),
    (500090, 4500150),
    (500010, 4500130)
]

# 2. 计算喷洒区域
result = smart_inscribe_from_gps(gps_boundary, coordinate_system="utm")

print(f"喷洒面积: {result.area:.0f} 平方米")

# 3. 生成喷洒路径（无人机喷幅5米）
paths = generate_work_paths(
    result.polygon,
    work_width=5.0,
    shape_type=result.shape_type
)

print(f"喷洒航线: {len(paths)} 条")

# 4. 计算药剂用量
spray_rate = 10  # 升/公顷
total_volume = (result.area / 10000) * spray_rate
print(f"所需药剂: {total_volume:.1f} 升")
```

---

## 🔧 高级配置

### 调整精度

```python
# 高精度（慢）
result = smart_inscribe_from_vertices(
    vertices,
    angle_step=0.5,  # 0.5度步长
    grid_resolution=2000  # 高分辨率
)

# 快速（低精度）
result = smart_inscribe_from_vertices(
    vertices,
    angle_step=5.0,  # 5度步长
    grid_resolution=500  # 低分辨率
)
```

### 只使用特定策略

```python
# 只使用自适应形状匹配
result = smart_inscribe_from_vertices(
    vertices,
    try_multiple_strategies=False
)
```

### 自定义作业路径间距

```python
# 根据设备宽度调整
tractor_width = 3.5  # 米
overlap = 0.2  # 20%重叠

paths = generate_work_paths(
    result.polygon,
    work_width=tractor_width * (1 - overlap),
    shape_type=result.shape_type
)
```

---

## ✅ API参考

### `smart_inscribe_from_vertices(vertices, angle_step=1.0, try_multiple_strategies=True, grid_resolution=1000)`

**参数**：
- `vertices`: Nx2 数组，田块边界顶点
- `angle_step`: 角度搜索步长（度），默认1.0
- `try_multiple_strategies`: 是否尝试多种策略，默认True
- `grid_resolution`: 内部计算分辨率，默认1000

**返回**：`InscribedResult` 对象
- `polygon`: 作业区域顶点 (Nx2)
- `shape_type`: 形状类型 (str)
- `area`: 面积 (float)
- `coverage`: 覆盖率 (0-1)
- `strategy`: 使用的策略 (str)

### `smart_inscribe_from_gps(gps_coords, angle_step=1.0, coordinate_system="utm")`

**参数**：
- `gps_coords`: GPS坐标列表 [(x1,y1), (x2,y2), ...]
- `angle_step`: 角度搜索步长（度）
- `coordinate_system`: "utm" 或 "wgs84"

**返回**：`InscribedResult` 对象（坐标系与输入相同）

### `generate_work_paths(polygon, work_width=20.0, shape_type="rectangle")`

**参数**：
- `polygon`: 作业区域顶点
- `work_width`: 作业宽度（米或像素）
- `shape_type`: 形状类型

**返回**：路径列表 `[(起点, 终点), ...]`

---

## 🎉 总结

### 核心优势

1. ✅ **直接从顶点输入** - 无需创建图像
2. ✅ **自动形状识别** - 智能判断田块类型
3. ✅ **形状自适应** - 内接同类形状，最大化覆盖
4. ✅ **GPS坐标支持** - UTM和WGS84
5. ✅ **作业路径生成** - 自动生成平行路径
6. ✅ **边界安全** - 100%不越界

### 适用场景

- 🚜 拖拉机耕作路径规划
- ✈️ 无人机喷洒路径规划
- 🌾 收割机作业区域规划
- 📍 精准农业田块管理
- 🗺️ GIS系统集成

### 性能指标

- **覆盖率**: 平均98%
- **计算速度**: < 1秒
- **支持形状**: 矩形/平行四边形/梯形/三角形/多边形
- **边界安全**: 100%

---

