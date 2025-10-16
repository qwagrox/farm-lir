"""
Axis-aligned maximum inscribed rectangle computation using geometric methods.

This module computes the largest axis-aligned rectangle that fits inside a polygon
using exact geometric calculations, without relying on image rasterization.
"""

import numpy as np
from typing import Tuple, Optional
from .geometry_utils import (
    get_critical_y_values,
    compute_max_width_between_y,
    polygon_bounds
)


def compute_axis_aligned_max_rect(polygon: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Compute the maximum axis-aligned rectangle inscribed in a polygon.
    
    This uses a sweep-line algorithm that tests all combinations of critical y-values
    as potential rectangle boundaries.
    
    Args:
        polygon: Nx2 array of polygon vertices in order (clockwise or counter-clockwise)
    
    Returns:
        (x, y, width, height, area) where (x, y) is the bottom-left corner
    """
    # Get all critical y-values (vertex y-coordinates)
    y_values = get_critical_y_values(polygon)
    
    if len(y_values) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    best_rect = (0.0, 0.0, 0.0, 0.0, 0.0)
    best_area = 0.0
    
    # Try all pairs of y-values as rectangle top and bottom
    for i, y_bottom in enumerate(y_values):
        for j in range(i + 1, len(y_values)):
            y_top = y_values[j]
            height = y_top - y_bottom
            
            if height <= 0:
                continue
            
            # Find maximum width that fits in this height range
            width, x_left = compute_max_width_between_y(polygon, y_bottom, y_top)
            
            if width <= 0:
                continue
            
            area = width * height
            
            if area > best_area:
                best_area = area
                best_rect = (x_left, y_bottom, width, height, area)
    
    return best_rect


def compute_axis_aligned_max_rect_optimized(polygon: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Optimized version using dynamic programming approach.
    
    For each bottom y-value, we incrementally update the width as we move the top upward.
    This reduces redundant intersection calculations.
    
    Args:
        polygon: Nx2 array of polygon vertices
    
    Returns:
        (x, y, width, height, area)
    """
    y_values = get_critical_y_values(polygon)
    
    if len(y_values) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    best_rect = (0.0, 0.0, 0.0, 0.0, 0.0)
    best_area = 0.0
    
    # For each bottom position
    for i, y_bottom in enumerate(y_values[:-1]):
        # Try each top position above it
        for j in range(i + 1, len(y_values)):
            y_top = y_values[j]
            height = y_top - y_bottom
            
            # Compute width for this height range
            width, x_left = compute_max_width_between_y(polygon, y_bottom, y_top)
            
            if width > 0:
                area = width * height
                if area > best_area:
                    best_area = area
                    best_rect = (x_left, y_bottom, width, height, area)
    
    return best_rect


def compute_axis_aligned_max_rect_with_sampling(polygon: np.ndarray, 
                                                 num_samples: int = 20) -> Tuple[float, float, float, float, float]:
    """
    Version with additional y-sampling for better accuracy on smooth polygons.
    
    Args:
        polygon: Nx2 array of polygon vertices
        num_samples: Number of additional samples between y_min and y_max
    
    Returns:
        (x, y, width, height, area)
    """
    # Get critical y-values from vertices
    y_values = set(get_critical_y_values(polygon))
    
    # Add uniformly sampled y-values
    x_min, y_min, x_max, y_max = polygon_bounds(polygon)
    for i in range(num_samples + 1):
        y = y_min + (y_max - y_min) * i / num_samples
        y_values.add(y)
    
    y_values = sorted(y_values)
    
    if len(y_values) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    best_rect = (0.0, 0.0, 0.0, 0.0, 0.0)
    best_area = 0.0
    
    # Try all pairs
    for i, y_bottom in enumerate(y_values):
        for j in range(i + 1, len(y_values)):
            y_top = y_values[j]
            height = y_top - y_bottom
            
            if height <= 1e-6:  # Skip very small heights
                continue
            
            width, x_left = compute_max_width_between_y(polygon, y_bottom, y_top)
            
            if width > 1e-6:  # Skip very small widths
                area = width * height
                if area > best_area:
                    best_area = area
                    best_rect = (x_left, y_bottom, width, height, area)
    
    return best_rect

