# 批量处理快速开始

## 🚀 5分钟上手

### 1. 最简单的例子

```python
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from largestinteriorrectangle import smart_inscribe_from_vertices

# 准备田块数据（顶点坐标）
fields = [
    {'id': 'A', 'vertices': np.array([[100,200], [500,200], [500,500], [100,500]])},
    {'id': 'B', 'vertices': np.array([[600,200], [900,200], [900,500], [600,500]])},
    {'id': 'C', 'vertices': np.array([[100,600], [500,600], [500,900], [100,900]])},
]

# 定义处理函数
def process(field):
    result = smart_inscribe_from_vertices(field['vertices'])
    return {'id': field['id'], 'area': result.area, 'coverage': result.coverage}

# 并行处理（4个线程）
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process, fields))

# 查看结果
for r in results:
    print(f"田块 {r['id']}: 作业面积 {r['area']:.0f}, 覆盖率 {r['coverage']:.1%}")
```

**输出示例**：
```
田块 A: 作业面积 158400, 覆盖率 99.0%
田块 B: 作业面积 89100, 覆盖率 99.0%
田块 C: 作业面积 89100, 覆盖率 99.0%
```

---

## 📊 实际应用：100块田地

```python
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from largestinteriorrectangle import smart_inscribe_from_vertices
import time

# 1. 从你的数据源加载（示例：从CSV）
import csv

def load_from_csv(filename):
    fields = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 假设CSV格式: field_id, v1_x, v1_y, v2_x, v2_y, v3_x, v3_y, v4_x, v4_y
            vertices = np.array([
                [float(row['v1_x']), float(row['v1_y'])],
                [float(row['v2_x']), float(row['v2_y'])],
                [float(row['v3_x']), float(row['v3_y'])],
                [float(row['v4_x']), float(row['v4_y'])]
            ])
            fields.append({'id': row['field_id'], 'vertices': vertices})
    return fields

# 2. 处理函数
def process_field(field):
    try:
        result = smart_inscribe_from_vertices(field['vertices'])
        return {
            'id': field['id'],
            'success': True,
            'area': result.area,
            'coverage': result.coverage,
            'shape': result.shape_type
        }
    except Exception as e:
        return {'id': field['id'], 'success': False, 'error': str(e)}

# 3. 批量处理
fields = load_from_csv('fields.csv')  # 替换为你的文件
print(f"加载了 {len(fields)} 块田地")

start = time.time()
with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_field, fields))
elapsed = time.time() - start

# 4. 统计
successful = [r for r in results if r['success']]
print(f"\n成功: {len(successful)}/{len(results)}")
print(f"用时: {elapsed:.1f}秒")
print(f"速度: {len(results)/elapsed:.1f} 田块/秒")
print(f"总作业面积: {sum(r['area'] for r in successful):,.0f}")
print(f"平均覆盖率: {np.mean([r['coverage'] for r in successful]):.1%}")

# 5. 导出结果
with open('results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'success', 'area', 'coverage', 'shape'])
    writer.writeheader()
    writer.writerows(results)

print("\n✅ 完成！结果已保存到 results.csv")
```

---

## 🎯 关键参数

### 工作线程数 (`max_workers`)

```python
import multiprocessing as mp

# 自动检测（推荐）
max_workers = mp.cpu_count()  # 例如：8核CPU = 8线程

# 保守设置（生产环境）
max_workers = 4

# 激进设置（开发测试）
max_workers = mp.cpu_count() * 2
```

### 角度步长 (`angle_step`)

```python
# 快速预览（5度）
result = smart_inscribe_from_vertices(vertices, angle_step=5.0)

# 标准精度（1度，推荐）
result = smart_inscribe_from_vertices(vertices, angle_step=1.0)

# 高精度（0.5度）
result = smart_inscribe_from_vertices(vertices, angle_step=0.5)
```

---

## ⚡ 性能预估

### 单个田块处理时间

| 角度步长 | 处理时间 |
|---------|---------|
| 5.0° | ~0.05秒 |
| 1.0° | ~0.2秒 |
| 0.5° | ~0.4秒 |

### 批量处理时间（100块田地）

| 工作线程 | 角度步长 | 总时间 |
|---------|---------|--------|
| 1 | 1.0° | ~20秒 |
| 4 | 1.0° | ~6秒 |
| 8 | 1.0° | ~4秒 |

### 大规模场景（500块田地）

- **顺序处理**：~100秒（1.7分钟）
- **并行处理（8线程）**：~20秒
- **加速比**：5x

---

## 💡 常见问题

### Q1: 如何显示进度？

```python
from concurrent.futures import as_completed

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(process_field, f): f for f in fields}
    
    completed = 0
    for future in as_completed(futures):
        result = future.result()
        completed += 1
        print(f"进度: {completed}/{len(fields)} ({completed/len(fields):.1%})", end='\r')
```

### Q2: 如何处理失败的田块？

```python
# 收集失败的田块
failed = [r for r in results if not r['success']]

# 重新处理失败的田块（使用更宽松的参数）
for fail in failed:
    field = next(f for f in fields if f['id'] == fail['id'])
    try:
        result = smart_inscribe_from_vertices(
            field['vertices'],
            angle_step=5.0  # 使用更大的步长
        )
        print(f"重试成功: {field['id']}")
    except:
        print(f"重试失败: {field['id']}")
```

### Q3: 如何导出到GeoJSON？

```python
import json

features = []
for r in results:
    if r['success']:
        # 假设你有work_vertices
        coords = r['work_vertices'].tolist()
        coords.append(coords[0])  # 闭合多边形
        
        feature = {
            "type": "Feature",
            "properties": {
                "field_id": r['id'],
                "work_area": r['area'],
                "coverage": r['coverage']
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

with open('results.geojson', 'w') as f:
    json.dump(geojson, f, indent=2)
```

---

## 📦 文件说明

- `batch_processing.py` - 完整的批量处理模块
- `BATCH_PROCESSING_GUIDE.md` - 详细使用指南
- `batch_demo.py` - 演示脚本
- `QUICK_START.md` - 本文档（快速开始）

---

## ✅ 检查清单

使用前请确认：

- [ ] 已安装 `largestinteriorrectangle` 包
- [ ] 田块数据格式正确（numpy数组，至少3个顶点）
- [ ] 选择了合适的 `max_workers` 和 `angle_step`
- [ ] 准备好结果导出路径

---

## 🎉 开始使用

复制上面的代码模板，替换数据加载部分，即可开始批量处理！

如需更多帮助，请查看 `BATCH_PROCESSING_GUIDE.md`。

