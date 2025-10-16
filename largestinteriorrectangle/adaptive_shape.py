"""
Adaptive Shape Inscribed Polygon Algorithm

Automatically selects the best inscribed shape based on field shape:
- Rectangle → Rectangle
- Parallelogram → Parallelogram  
- Trapezoid → Trapezoid
- Triangle → Triangle
- General polygon → Optimized convex polygon
"""

import numpy as np
import cv2
from typing import Tuple, Optional, List
from enum import Enum


class ShapeType(Enum):
    """Shape classification"""
    TRIANGLE = "triangle"
    RECTANGLE = "rectangle"
    PARALLELOGRAM = "parallelogram"
    TRAPEZOID = "trapezoid"
    GENERAL = "general"


def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate angle between two vectors in degrees."""
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))


def are_parallel(v1: np.ndarray, v2: np.ndarray, tolerance: float = 5.0) -> bool:
    """Check if two vectors are parallel (within tolerance degrees)."""
    angle = angle_between_vectors(v1, v2)
    return angle < tolerance or abs(angle - 180) < tolerance


def are_perpendicular(v1: np.ndarray, v2: np.ndarray, tolerance: float = 5.0) -> bool:
    """Check if two vectors are perpendicular (within tolerance degrees)."""
    angle = angle_between_vectors(v1, v2)
    return abs(angle - 90) < tolerance


def classify_shape(polygon: np.ndarray, angle_tolerance: float = 5.0) -> ShapeType:
    """
    Classify polygon shape based on geometric properties.
    
    Args:
        polygon: Nx2 array of vertices
        angle_tolerance: Tolerance for angle comparisons (degrees)
    
    Returns:
        ShapeType enum
    """
    n = len(polygon)
    
    # Triangle
    if n == 3:
        return ShapeType.TRIANGLE
    
    # Quadrilateral
    if n == 4:
        # Get edges
        edges = []
        for i in range(4):
            v = polygon[(i + 1) % 4] - polygon[i]
            edges.append(v / (np.linalg.norm(v) + 1e-10))
        
        # Check for parallel pairs
        parallel_pairs = []
        for i in range(4):
            for j in range(i + 1, 4):
                if are_parallel(edges[i], edges[j], angle_tolerance):
                    parallel_pairs.append((i, j))
        
        # Two pairs of parallel edges → Parallelogram or Rectangle
        if len(parallel_pairs) >= 2:
            # Check if all angles are 90°
            all_right_angles = True
            for i in range(4):
                angle = angle_between_vectors(edges[i], edges[(i + 1) % 4])
                if abs(angle - 90) > angle_tolerance:
                    all_right_angles = False
                    break
            
            if all_right_angles:
                return ShapeType.RECTANGLE
            else:
                return ShapeType.PARALLELOGRAM
        
        # One pair of parallel edges → Trapezoid
        elif len(parallel_pairs) == 1:
            return ShapeType.TRAPEZOID
    
    # General polygon
    return ShapeType.GENERAL


def shrink_polygon_to_fit(polygon: np.ndarray, 
                          outer_polygon: np.ndarray,
                          max_iterations: int = 30) -> Tuple[np.ndarray, float]:
    """
    Shrink polygon towards center until it fits inside outer polygon.
    
    Args:
        polygon: Inner polygon vertices
        outer_polygon: Outer boundary polygon
        max_iterations: Max binary search iterations
    
    Returns:
        fitted_polygon: Adjusted polygon
        area: Area of fitted polygon
    """
    center = polygon.mean(axis=0)
    
    # Check if already inside
    all_inside = True
    for point in polygon:
        result = cv2.pointPolygonTest(
            outer_polygon.astype(np.float32),
            tuple(point.astype(float)),
            True
        )
        if result < 1.0:  # Safety margin (increased to 1.0 pixel)
            all_inside = False
            break
    
    if all_inside:
        area = cv2.contourArea(polygon.astype(np.float32))
        return polygon, area
    
    # Binary search for shrink factor
    low, high = 0.5, 1.0
    best_polygon = None
    best_area = 0.0
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        test_polygon = center + (polygon - center) * mid
        
        # Check all points
        all_inside = True
        for point in test_polygon:
            result = cv2.pointPolygonTest(
                outer_polygon.astype(np.float32),
                tuple(point.astype(float)),
                True
            )
            if result < 1.0:
                all_inside = False
                break
        
        if all_inside:
            area = cv2.contourArea(test_polygon.astype(np.float32))
            if area > best_area:
                best_area = area
                best_polygon = test_polygon.copy()
            low = mid
        else:
            high = mid
        
        if high - low < 0.001:
            break
    
    if best_polygon is None:
        return polygon * 0.5, 0.0
    
    return best_polygon, best_area


def inscribe_parallelogram(polygon: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Find maximum inscribed parallelogram in a parallelogram.
    
    Strategy: Shrink uniformly while maintaining parallelogram shape.
    """
    if len(polygon) != 4:
        raise ValueError("Parallelogram must have 4 vertices")
    
    # Simply shrink towards center
    best_polygon, best_area = shrink_polygon_to_fit(polygon, polygon)
    
    return best_polygon, best_area


def inscribe_trapezoid(polygon: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Find maximum inscribed trapezoid in a trapezoid.
    
    Strategy: Shrink while maintaining trapezoid proportions.
    """
    if len(polygon) != 4:
        raise ValueError("Trapezoid must have 4 vertices")
    
    # Shrink uniformly
    best_polygon, best_area = shrink_polygon_to_fit(polygon, polygon)
    
    return best_polygon, best_area


def inscribe_triangle(polygon: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Find maximum inscribed triangle in a triangle.
    
    Strategy: Shrink towards incenter.
    """
    if len(polygon) != 3:
        raise ValueError("Triangle must have 3 vertices")
    
    # Calculate incenter (weighted by edge lengths)
    a = np.linalg.norm(polygon[1] - polygon[2])
    b = np.linalg.norm(polygon[2] - polygon[0])
    c = np.linalg.norm(polygon[0] - polygon[1])
    
    incenter = (a * polygon[0] + b * polygon[1] + c * polygon[2]) / (a + b + c)
    
    # Binary search for shrink factor
    low, high = 0.5, 1.0
    best_polygon = None
    best_area = 0.0
    
    for _ in range(30):
        mid = (low + high) / 2
        test_polygon = incenter + (polygon - incenter) * mid
        
        # Check if inside
        all_inside = True
        for point in test_polygon:
            result = cv2.pointPolygonTest(
                polygon.astype(np.float32),
                tuple(point.astype(float)),
                True
            )
            if result < 1.0:
                all_inside = False
                break
        
        if all_inside:
            area = cv2.contourArea(test_polygon.astype(np.float32))
            if area > best_area:
                best_area = area
                best_polygon = test_polygon.copy()
            low = mid
        else:
            high = mid
        
        if high - low < 0.001:
            break
    
    if best_polygon is None:
        return polygon * 0.5, 0.0
    
    return best_polygon, best_area


def adaptive_inscribed_polygon(grid: np.ndarray,
                               angle_tolerance: float = 5.0,
                               epsilon_factor: float = 0.01) -> Tuple[np.ndarray, ShapeType, float]:
    """
    Find maximum inscribed polygon with adaptive shape matching.
    
    Args:
        grid: Binary grid
        angle_tolerance: Tolerance for angle comparisons (degrees)
        epsilon_factor: Polygon approximation factor
    
    Returns:
        polygon: Vertices of inscribed polygon
        shape_type: Detected shape type
        area: Area of inscribed polygon
    """
    # Extract contour
    contours, _ = cv2.findContours(
        grid.astype(np.uint8) * 255,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return np.zeros((4, 2)), ShapeType.GENERAL, 0.0
    
    contour = max(contours, key=cv2.contourArea)
    
    # Approximate polygon
    perimeter = cv2.arcLength(contour, True)
    epsilon = epsilon_factor * perimeter
    polygon = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2).astype(np.float64)
    
    # Classify shape
    shape_type = classify_shape(polygon, angle_tolerance)
    
    print(f"Detected shape: {shape_type.value}, vertices: {len(polygon)}")
    
    # Apply appropriate inscribed algorithm
    if shape_type == ShapeType.TRIANGLE:
        inscribed, area = inscribe_triangle(polygon)
    elif shape_type == ShapeType.RECTANGLE or shape_type == ShapeType.PARALLELOGRAM:
        inscribed, area = inscribe_parallelogram(polygon)
    elif shape_type == ShapeType.TRAPEZOID:
        inscribed, area = inscribe_trapezoid(polygon)
    else:
        # General polygon: shrink uniformly
        inscribed, area = shrink_polygon_to_fit(polygon, polygon)
    
    return inscribed, shape_type, area

