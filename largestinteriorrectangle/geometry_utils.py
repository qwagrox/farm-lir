"""
Geometric utility functions for precise LIR computation.

This module provides exact geometric calculations without image rotation,
avoiding interpolation errors and pixel discretization issues.
"""

import numpy as np
from typing import Tuple, List, Optional


def rotate_point(point: np.ndarray, angle_rad: float, center: np.ndarray = None) -> np.ndarray:
    """
    Rotate a point around a center by a given angle.
    
    Args:
        point: 2D point as [x, y]
        angle_rad: Rotation angle in radians
        center: Center of rotation, defaults to origin
    
    Returns:
        Rotated point as [x, y]
    """
    if center is None:
        center = np.array([0.0, 0.0])
    
    # Translate to origin
    p = point - center
    
    # Rotate
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    x_new = p[0] * cos_a - p[1] * sin_a
    y_new = p[0] * sin_a + p[1] * cos_a
    
    # Translate back
    return np.array([x_new, y_new]) + center


def rotate_polygon(polygon: np.ndarray, angle_rad: float, center: np.ndarray = None) -> np.ndarray:
    """
    Rotate a polygon around a center by a given angle.
    
    Args:
        polygon: Nx2 array of polygon vertices
        angle_rad: Rotation angle in radians
        center: Center of rotation, defaults to polygon centroid
    
    Returns:
        Rotated polygon as Nx2 array
    """
    if center is None:
        center = polygon.mean(axis=0)
    
    rotated = np.array([rotate_point(p, angle_rad, center) for p in polygon])
    return rotated


def polygon_bounds(polygon: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Get the bounding box of a polygon.
    
    Args:
        polygon: Nx2 array of polygon vertices
    
    Returns:
        (x_min, y_min, x_max, y_max)
    """
    x_min = polygon[:, 0].min()
    x_max = polygon[:, 0].max()
    y_min = polygon[:, 1].min()
    y_max = polygon[:, 1].max()
    
    return x_min, y_min, x_max, y_max


def line_intersection(p1: np.ndarray, p2: np.ndarray, 
                      p3: np.ndarray, p4: np.ndarray) -> Optional[np.ndarray]:
    """
    Find intersection point of two line segments.
    
    Args:
        p1, p2: Endpoints of first line segment
        p3, p4: Endpoints of second line segment
    
    Returns:
        Intersection point as [x, y], or None if no intersection
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-10:
        return None  # Parallel or coincident
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return np.array([x, y])
    
    return None


def point_in_polygon(point: np.ndarray, polygon: np.ndarray) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm.
    
    Args:
        point: 2D point as [x, y]
        polygon: Nx2 array of polygon vertices
    
    Returns:
        True if point is inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        
        p1x, p1y = p2x, p2y
    
    return inside


def horizontal_line_polygon_intersection(polygon: np.ndarray, y: float) -> List[float]:
    """
    Find all x-coordinates where a horizontal line intersects a polygon.
    
    Args:
        polygon: Nx2 array of polygon vertices
        y: Y-coordinate of the horizontal line
    
    Returns:
        List of x-coordinates sorted in ascending order
    """
    intersections = []
    n = len(polygon)
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        
        y1, y2 = p1[1], p2[1]
        
        # Check if edge crosses the horizontal line
        if (y1 <= y < y2) or (y2 <= y < y1):
            # Calculate x-coordinate of intersection
            x1, x2 = p1[0], p2[0]
            if abs(y2 - y1) > 1e-10:
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                intersections.append(x)
        elif abs(y1 - y) < 1e-10:
            # Edge endpoint is exactly on the line
            # Only add if it's a crossing (not just touching)
            y_prev = polygon[(i - 1) % n][1]
            y_next = p2[1]
            if (y_prev < y < y_next) or (y_next < y < y_prev):
                intersections.append(p1[0])
    
    return sorted(intersections)


def get_critical_y_values(polygon: np.ndarray) -> List[float]:
    """
    Get all critical y-values for the polygon (vertex y-coordinates).
    
    Args:
        polygon: Nx2 array of polygon vertices
    
    Returns:
        Sorted list of unique y-values
    """
    y_values = sorted(set(polygon[:, 1]))
    return y_values


def compute_max_width_between_y(polygon: np.ndarray, y_bottom: float, y_top: float) -> Tuple[float, float]:
    """
    Compute the maximum width of the polygon between two y-coordinates.
    
    This finds the widest horizontal span that fits completely inside the polygon
    for all y-values in [y_bottom, y_top].
    
    Args:
        polygon: Nx2 array of polygon vertices
        y_bottom: Bottom y-coordinate
        y_top: Top y-coordinate
    
    Returns:
        (max_width, x_left) where max_width is the maximum width and x_left is the left x-coordinate
    """
    # Sample y-values in the range
    y_values = get_critical_y_values(polygon)
    y_values = [y for y in y_values if y_bottom <= y <= y_top]
    
    # Also sample intermediate points for better accuracy
    num_samples = 10
    for i in range(num_samples + 1):
        y = y_bottom + (y_top - y_bottom) * i / num_samples
        if y not in y_values:
            y_values.append(y)
    
    y_values = sorted(y_values)
    
    if not y_values:
        return 0.0, 0.0
    
    # Find the minimum width across all y-values
    min_width = float('inf')
    best_x_left = 0.0
    
    for y in y_values:
        intersections = horizontal_line_polygon_intersection(polygon, y)
        
        if len(intersections) < 2:
            return 0.0, 0.0  # No valid width at this y
        
        # Find the widest span (should be between first and last intersection for convex polygons)
        x_left = intersections[0]
        x_right = intersections[-1]
        width = x_right - x_left
        
        if width < min_width:
            min_width = width
            best_x_left = x_left
    
    return min_width, best_x_left


def rectangle_corners(x: float, y: float, width: float, height: float, 
                      angle_rad: float = 0.0) -> np.ndarray:
    """
    Get the four corners of a rectangle.
    
    Args:
        x, y: Bottom-left corner (before rotation)
        width, height: Rectangle dimensions
        angle_rad: Rotation angle in radians
    
    Returns:
        4x2 array of corner coordinates
    """
    corners = np.array([
        [x, y],
        [x + width, y],
        [x + width, y + height],
        [x, y + height]
    ])
    
    if abs(angle_rad) > 1e-10:
        center = corners.mean(axis=0)
        corners = rotate_polygon(corners, angle_rad, center)
    
    return corners





def point_in_polygon(point: np.ndarray, polygon: np.ndarray) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm.
    
    Args:
        point: 2D point as [x, y]
        polygon: Nx2 array of polygon vertices
    
    Returns:
        True if point is inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def rectangle_in_polygon(rect_corners: np.ndarray, polygon: np.ndarray, tolerance: float = 1e-3) -> bool:
    """
    Check if a rectangle is completely inside a polygon.
    
    Args:
        rect_corners: 4x2 array of rectangle corners
        polygon: Nx2 array of polygon vertices
        tolerance: Tolerance for boundary checking (negative = shrink rectangle slightly)
    
    Returns:
        True if rectangle is completely inside polygon
    """
    import cv2
    
    # Method 1: Check all corners
    for corner in rect_corners:
        if not point_in_polygon(corner, polygon):
            return False
    
    # Method 2: Check midpoints of edges (to catch edge intersections)
    for i in range(4):
        midpoint = (rect_corners[i] + rect_corners[(i + 1) % 4]) / 2
        if not point_in_polygon(midpoint, polygon):
            return False
    
    # Method 3: Use OpenCV contour containment (more robust)
    # Convert to int32 for OpenCV
    rect_int = rect_corners.astype(np.float32)
    polygon_int = polygon.astype(np.float32)
    
    # Check if rectangle vertices are inside polygon
    for corner in rect_int:
        dist = cv2.pointPolygonTest(polygon_int, tuple(corner), True)
        if dist < -tolerance:  # Negative means outside
            return False
    
    return True


def shrink_rectangle(rect_corners: np.ndarray, shrink_factor: float = 0.99) -> np.ndarray:
    """
    Shrink a rectangle towards its center.
    
    Args:
        rect_corners: 4x2 array of rectangle corners
        shrink_factor: Factor to shrink (0.99 = 99% of original size)
    
    Returns:
        Shrunken rectangle corners
    """
    center = rect_corners.mean(axis=0)
    shrunken = center + (rect_corners - center) * shrink_factor
    return shrunken

