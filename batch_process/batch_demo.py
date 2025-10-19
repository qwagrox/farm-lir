#!/usr/bin/env python3
"""
Quick Batch Processing Demo - Fast version for demonstration
"""

import numpy as np
import sys
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/home/ubuntu/lir')

from largestinteriorrectangle import smart_inscribe_from_vertices


def create_field(field_id, rotation=0):
    """Create a simple rectangular field"""
    width, height = 300, 200
    center = np.array([500, 500])
    
    vertices = np.array([
        [-width/2, -height/2],
        [width/2, -height/2],
        [width/2, height/2],
        [-width/2, height/2]
    ])
    
    # Rotate
    angle_rad = np.radians(rotation)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    vertices = vertices @ rotation_matrix.T + center
    
    return {'id': field_id, 'vertices': vertices}


def process_field(field):
    """Process one field"""
    start = time.time()
    result = smart_inscribe_from_vertices(field['vertices'], angle_step=5.0)
    return {
        'id': field['id'],
        'area': result.area,
        'coverage': result.coverage,
        'time': time.time() - start
    }


print("="*60)
print("QUICK BATCH PROCESSING DEMO")
print("="*60)

# Create 20 fields with different rotations
print("\n📍 Creating 20 fields...")
fields = [create_field(f"FIELD_{i+1:02d}", rotation=i*9) for i in range(20)]
print(f"   ✅ Created {len(fields)} fields")

# Sequential
print("\n⏱️  Sequential processing...")
start = time.time()
seq_results = [process_field(f) for f in fields]
seq_time = time.time() - start
print(f"   ✅ Done in {seq_time:.2f}s")

# Parallel
print("\n🚀 Parallel processing (4 workers)...")
start = time.time()
with ThreadPoolExecutor(max_workers=4) as executor:
    par_results = list(executor.map(process_field, fields))
par_time = time.time() - start
print(f"   ✅ Done in {par_time:.2f}s")

# Results
avg_coverage = np.mean([r['coverage'] for r in par_results])
total_area = sum(r['area'] for r in par_results)

print(f"\n📊 Results:")
print(f"   Fields processed: {len(fields)}")
print(f"   Total work area: {total_area:,.0f} sq.units")
print(f"   Average coverage: {avg_coverage:.1%}")
print(f"   Sequential time: {seq_time:.2f}s")
print(f"   Parallel time: {par_time:.2f}s")
print(f"   Speedup: {seq_time/par_time:.2f}x")
print(f"   Throughput: {len(fields)/par_time:.1f} fields/sec")

print(f"\n💡 For a 500-field farm:")
print(f"   Estimated time (sequential): {seq_time * 500 / len(fields):.1f}s ({seq_time * 500 / len(fields) / 60:.1f} min)")
print(f"   Estimated time (parallel): {par_time * 500 / len(fields):.1f}s ({par_time * 500 / len(fields) / 60:.1f} min)")
print(f"   Time saved: {(seq_time - par_time) * 500 / len(fields):.1f}s ({(seq_time - par_time) * 500 / len(fields) / 60:.1f} min)")

print(f"\n{'='*60}")
print("✅ DEMO COMPLETE!")
print(f"{'='*60}")

