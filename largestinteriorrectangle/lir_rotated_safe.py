"""
Boundary-safe version of rotated LIR.

Based on lir_rotated.py but with guaranteed boundary compliance.
"""

import numpy as np
import cv2
from typing import Tuple
from .lir_basis import largest_interior_rectangle as lir_basis


def shrink_rect_to_polygon(corners: np.ndarray, 
                           polygon: np.ndarray,
                           max_iterations: int = 30) -> Tuple[np.ndarray, float]:
    """
    Shrink rectangle until all corners are inside polygon.
    
    Args:
        corners: 4x2 array of rectangle corners
        polygon: Nx2 array of polygon vertices
    
    Returns:
        shrunken_corners: Adjusted corners
        area: Area of shrunken rectangle
    """
    center = corners.mean(axis=0)
    
    # Check if all corners are inside (with small safety margin)
    safety_margin = 0.5  # pixels
    all_inside = True
    for corner in corners:
        result = cv2.pointPolygonTest(polygon.astype(np.float32), tuple(corner.astype(float)), True)  # True for signed distance
        if result < safety_margin:  # Outside or too close to boundary
            all_inside = False
            break
    
    if all_inside:
        area = cv2.contourArea(corners.astype(np.float32))
        return corners, area
    
    # Binary search for shrink factor
    low, high = 0.5, 1.0
    best_corners = None
    best_area = 0.0
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        test_corners = center + (corners - center) * mid
        
        # Check all corners with safety margin
        all_inside = True
        for corner in test_corners:
            result = cv2.pointPolygonTest(polygon.astype(np.float32), tuple(corner.astype(float)), True)  # True for signed distance
            if result < safety_margin:
                all_inside = False
                break
        
        if all_inside:
            area = cv2.contourArea(test_corners.astype(np.float32))
            if area > best_area:
                best_area = area
                best_corners = test_corners.copy()
            low = mid
        else:
            high = mid
        
        if high - low < 0.001:
            break
    
    if best_corners is None:
        return corners * 0.5, 0.0  # Fallback
    
    return best_corners, best_area


def lir_rotated_safe(grid: np.ndarray,
                     angle_step: float = 1.0,
                     epsilon_factor: float = 0.01) -> Tuple[np.ndarray, float, float]:
    """
    Boundary-safe rotated LIR.
    
    Args:
        grid: Binary grid
        angle_step: Angle step in degrees
        epsilon_factor: Polygon approximation factor
    
    Returns:
        corners: 4x2 array of rectangle corners
        angle: Optimal angle in degrees
        area: Area of rectangle
    """
    # Extract polygon
    contours, _ = cv2.findContours(
        grid.astype(np.uint8) * 255,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return np.zeros((4, 2)), 0.0, 0.0
    
    contour = max(contours, key=cv2.contourArea)
    
    # Approximate polygon
    perimeter = cv2.arcLength(contour, True)
    epsilon = epsilon_factor * perimeter
    polygon = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2).astype(np.float64)
    
    # Get candidate angles
    angles = []
    n = len(polygon)
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        length = np.sqrt(dx**2 + dy**2)
        if length < 1e-6:
            continue
        
        angle_rad = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle_rad) % 180
        
        angles.append(angle_deg)
        angles.append((angle_deg + 90) % 180)
    
    # Add sampled angles
    num_samples = int(180 / angle_step)
    for i in range(num_samples):
        angles.append(i * angle_step)
    
    # Remove duplicates
    unique_angles = []
    tolerance = angle_step / 2
    
    for angle in angles:
        is_duplicate = False
        for existing in unique_angles:
            diff = abs(angle - existing)
            if diff < tolerance or abs(diff - 180) < tolerance:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_angles.append(angle)
    
    best_corners = None
    best_angle = 0.0
    best_area = 0.0
    
    # Grid dimensions
    h, w = grid.shape
    center = (w / 2, h / 2)
    
    # Test each angle
    for angle_deg in unique_angles:
        # Rotate grid
        M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
        
        # Calculate new dimensions
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust rotation matrix
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Rotate grid
        rotated_grid = cv2.warpAffine(
            grid.astype(np.uint8),
            M,
            (new_w, new_h),
            borderValue=0
        ).astype(bool)
        
        # Compute axis-aligned LIR
        try:
            rect = lir_basis(rotated_grid)
            
            if rect is None or len(rect) != 4:
                continue
            
            x, y, w_rect, h_rect = rect
            
            if w_rect <= 0 or h_rect <= 0:
                continue
            
            # Create corners in rotated space
            corners_rot = np.array([
                [x, y],
                [x + w_rect, y],
                [x + w_rect, y + h_rect],
                [x, y + h_rect]
            ], dtype=np.float32)
            
            # Rotate back
            M_inv = cv2.invertAffineTransform(M)
            corners_homogeneous = np.hstack([corners_rot, np.ones((4, 1))])
            corners_original = (M_inv @ corners_homogeneous.T).T
            
            # Shrink to fit polygon
            fitted_corners, area = shrink_rect_to_polygon(corners_original, polygon)
            
            if area > best_area:
                best_area = area
                best_angle = angle_deg
                best_corners = fitted_corners
                
        except Exception:
            continue
    
    if best_corners is None:
        return np.zeros((4, 2)), 0.0, 0.0
    
    return best_corners, best_angle, best_area

