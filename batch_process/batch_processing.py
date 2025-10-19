#!/usr/bin/env python3
"""
Batch Processing Module for Large-Scale Farm Field Analysis

This module provides efficient parallel processing capabilities for analyzing
multiple farm fields simultaneously.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import time
import multiprocessing as mp

from .smart_inscribe import smart_inscribe_from_vertices, InscribedResult
from .smart_inscribe import generate_work_paths


@dataclass
class FieldInput:
    """Input data for a single field"""
    field_id: str
    vertices: np.ndarray
    work_width: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class FieldResult:
    """Result data for a single field"""
    field_id: str
    success: bool
    inscribed_result: Optional[InscribedResult] = None
    work_paths: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None
    computation_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


def process_single_field(field_input: FieldInput, 
                         angle_step: float = 1.0,
                         generate_paths: bool = True) -> FieldResult:
    """
    Process a single field (worker function for parallel processing)
    
    Args:
        field_input: Field input data
        angle_step: Angle search step in degrees
        generate_paths: Whether to generate work paths
        
    Returns:
        FieldResult object with computation results
    """
    start_time = time.time()
    
    try:
        # Compute inscribed polygon
        result = smart_inscribe_from_vertices(
            field_input.vertices,
            angle_step=angle_step,
            try_multiple_strategies=True
        )
        
        # Generate work paths if requested
        work_paths = None
        if generate_paths and field_input.work_width is not None:
            work_paths = generate_work_paths(
                result.polygon,
                work_width=field_input.work_width,
                shape_type=result.shape_type
            )
        
        computation_time = time.time() - start_time
        
        return FieldResult(
            field_id=field_input.field_id,
            success=True,
            inscribed_result=result,
            work_paths=work_paths,
            computation_time=computation_time,
            metadata=field_input.metadata
        )
        
    except Exception as e:
        computation_time = time.time() - start_time
        return FieldResult(
            field_id=field_input.field_id,
            success=False,
            computation_time=computation_time,
            error_message=str(e),
            metadata=field_input.metadata
        )


class BatchFieldProcessor:
    """
    High-performance batch processor for multiple farm fields
    
    Features:
    - Parallel processing using multiprocessing
    - Progress tracking
    - Error handling and retry
    - Result aggregation and statistics
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 angle_step: float = 1.0,
                 generate_paths: bool = True):
        """
        Initialize batch processor
        
        Args:
            max_workers: Maximum number of parallel workers (default: CPU count)
            angle_step: Angle search step in degrees
            generate_paths: Whether to generate work paths
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.angle_step = angle_step
        self.generate_paths = generate_paths
        
    def process_fields(self, 
                      fields: List[FieldInput],
                      progress_callback: Optional[Callable] = None) -> List[FieldResult]:
        """
        Process multiple fields in parallel
        
        Args:
            fields: List of field inputs
            progress_callback: Optional callback function(completed, total)
            
        Returns:
            List of field results
        """
        results = []
        total = len(fields)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_field = {
                executor.submit(
                    process_single_field,
                    field,
                    self.angle_step,
                    self.generate_paths
                ): field for field in fields
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_field):
                result = future.result()
                results.append(result)
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        
        # Sort results by field_id to maintain order
        results.sort(key=lambda r: r.field_id)
        
        return results
    
    def get_statistics(self, results: List[FieldResult]) -> Dict:
        """
        Compute statistics from batch results
        
        Args:
            results: List of field results
            
        Returns:
            Dictionary with statistics
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if not successful:
            return {
                'total_fields': len(results),
                'successful': 0,
                'failed': len(failed),
                'success_rate': 0.0
            }
        
        total_area = sum(r.inscribed_result.area for r in successful)
        avg_coverage = np.mean([r.inscribed_result.coverage for r in successful])
        total_time = sum(r.computation_time for r in results)
        avg_time = np.mean([r.computation_time for r in results])
        
        shape_counts = {}
        for r in successful:
            shape = r.inscribed_result.shape_type
            shape_counts[shape] = shape_counts.get(shape, 0) + 1
        
        return {
            'total_fields': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results),
            'total_work_area': total_area,
            'average_coverage': avg_coverage,
            'total_computation_time': total_time,
            'average_computation_time': avg_time,
            'throughput': len(results) / total_time if total_time > 0 else 0,
            'shape_distribution': shape_counts,
            'max_workers': self.max_workers
        }


def create_demo_farm(num_fields: int = 50) -> List[FieldInput]:
    """
    Create a demo farm with multiple fields for testing
    
    Args:
        num_fields: Number of fields to generate
        
    Returns:
        List of FieldInput objects
    """
    fields = []
    
    # Generate fields with various shapes and sizes
    for i in range(num_fields):
        # Random field parameters
        center_x = np.random.uniform(100, 900)
        center_y = np.random.uniform(100, 900)
        width = np.random.uniform(200, 400)
        height = np.random.uniform(150, 300)
        rotation = np.random.uniform(0, 180)
        
        # Random shape type
        shape_type = np.random.choice(['rectangle', 'parallelogram', 'trapezoid'])
        
        if shape_type == 'rectangle':
            # Rectangle
            vertices = np.array([
                [-width/2, -height/2],
                [width/2, -height/2],
                [width/2, height/2],
                [-width/2, height/2]
            ])
        elif shape_type == 'parallelogram':
            # Parallelogram
            shear = np.random.uniform(50, 100)
            vertices = np.array([
                [-width/2, -height/2],
                [width/2, -height/2],
                [width/2 + shear, height/2],
                [-width/2 + shear, height/2]
            ])
        else:  # trapezoid
            # Trapezoid
            top_width = width * np.random.uniform(0.6, 0.9)
            vertices = np.array([
                [-width/2, -height/2],
                [width/2, -height/2],
                [top_width/2, height/2],
                [-top_width/2, height/2]
            ])
        
        # Rotate
        angle_rad = np.radians(rotation)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
        vertices = vertices @ rotation_matrix.T
        
        # Translate to center
        vertices += np.array([center_x, center_y])
        
        # Create field input
        field = FieldInput(
            field_id=f"FIELD_{i+1:03d}",
            vertices=vertices,
            work_width=20.0,
            metadata={
                'shape_type': shape_type,
                'rotation': rotation,
                'area_estimate': width * height
            }
        )
        fields.append(field)
    
    return fields


def export_results_to_geojson(results: List[FieldResult], 
                               filename: str = "farm_results.geojson"):
    """
    Export results to GeoJSON format for GIS visualization
    
    Args:
        results: List of field results
        filename: Output filename
    """
    import json
    
    features = []
    
    for result in results:
        if not result.success:
            continue
        
        # Field boundary
        field_coords = result.inscribed_result.polygon.tolist()
        field_coords.append(field_coords[0])  # Close polygon
        
        feature = {
            "type": "Feature",
            "properties": {
                "field_id": result.field_id,
                "shape_type": result.inscribed_result.shape_type,
                "work_area": float(result.inscribed_result.area),
                "coverage": float(result.inscribed_result.coverage),
                "computation_time": float(result.computation_time)
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [field_coords]
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"✅ Exported {len(features)} fields to {filename}")


def export_results_to_csv(results: List[FieldResult],
                          filename: str = "farm_results.csv"):
    """
    Export results to CSV format for data analysis
    
    Args:
        results: List of field results
        filename: Output filename
    """
    import csv
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'field_id', 'success', 'shape_type', 'work_area',
            'coverage', 'num_paths', 'computation_time', 'error'
        ])
        
        # Data
        for result in results:
            if result.success:
                writer.writerow([
                    result.field_id,
                    'Yes',
                    result.inscribed_result.shape_type,
                    f"{result.inscribed_result.area:.2f}",
                    f"{result.inscribed_result.coverage:.3f}",
                    len(result.work_paths) if result.work_paths else 0,
                    f"{result.computation_time:.3f}",
                    ''
                ])
            else:
                writer.writerow([
                    result.field_id,
                    'No',
                    '',
                    '',
                    '',
                    '',
                    f"{result.computation_time:.3f}",
                    result.error_message
                ])
    
    print(f"✅ Exported {len(results)} fields to {filename}")

