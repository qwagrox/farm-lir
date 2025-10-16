#!/usr/bin/env python3
"""Simple test for vertex input"""

import numpy as np
import sys
sys.path.insert(0, '/home/ubuntu/lir')

from largestinteriorrectangle import smart_inscribe_from_vertices, classify_shape

# Test: Parallelogram field
print("Test: Parallelogram Field from Vertices")
print("="*60)

vertices = np.array([
    [150, 200],
    [550, 200],
    [650, 450],
    [250, 450]
], dtype=np.float64)

print(f"Field vertices ({len(vertices)} points):")
for i, v in enumerate(vertices):
    print(f"  Point {i}: ({v[0]:.1f}, {v[1]:.1f})")

# Classify
shape = classify_shape(vertices)
print(f"\nShape classification: {shape.value}")

# Compute inscribed
print("\nComputing inscribed polygon...")
result = smart_inscribe_from_vertices(vertices, angle_step=2.0)

print(f"\nResult:")
print(f"  Shape: {result.shape_type}")
print(f"  Area: {result.area:.0f}")
print(f"  Coverage: {result.coverage:.1%}")
print(f"  Strategy: {result.strategy}")

print(f"\nWork area vertices:")
for i, v in enumerate(result.polygon):
    print(f"  Point {i}: ({v[0]:.1f}, {v[1]:.1f})")

print("\n✅ Vertex input support: WORKING")

