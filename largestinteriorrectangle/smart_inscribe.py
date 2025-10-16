"""
Smart Inscribed Polygon with Multi-Strategy Optimization

Compares multiple strategies and selects the best one:
1. Adaptive shape matching (parallelogram → parallelogram)
2. Forced rectangle (fallback)
3. Hybrid approach

Maximizes coverage while ensuring boundary compliance.
"""

import numpy as np
import cv2
from typing import Tuple, Dict, List
from .adaptive_shape import adaptive_inscribed_polygon, ShapeType
from .lir_rotated_safe import lir_rotated_safe


class InscribedResult:
    """Result of inscribed polygon calculation"""
    
    def __init__(self, polygon: np.ndarray, shape_type: str, area: float, 
                 coverage: float, strategy: str):
        self.polygon = polygon
        self.shape_type = shape_type
        self.area = area
        self.coverage = coverage
        self.strategy = strategy
    
    def __repr__(self):
        return (f"InscribedResult(shape={self.shape_type}, area={self.area:.0f}, "
                f"coverage={self.coverage:.1%}, strategy={self.strategy})")


def compute_coverage(inscribed_area: float, field_area: float) -> float:
    """Compute coverage ratio."""
    if field_area == 0:
        return 0.0
    return inscribed_area / field_area


def smart_inscribe(grid: np.ndarray,
                   angle_step: float = 1.0,
                   try_multiple_strategies: bool = True) -> InscribedResult:
    """
    Smart inscribed polygon with multi-strategy optimization.
    
    Args:
        grid: Binary grid of field
        angle_step: Angle step for rectangle search (degrees)
        try_multiple_strategies: If True, try multiple strategies and pick best
    
    Returns:
        InscribedResult with best inscribed polygon
    """
    field_area = grid.sum()
    
    if field_area == 0:
        return InscribedResult(
            np.zeros((4, 2)), "empty", 0.0, 0.0, "none"
        )
    
    results = []
    
    # Strategy 1: Adaptive shape matching
    try:
        polygon, shape_type, area = adaptive_inscribed_polygon(
            grid, 
            angle_tolerance=5.0,
            epsilon_factor=0.01
        )
        
        coverage = compute_coverage(area, field_area)
        
        results.append(InscribedResult(
            polygon,
            shape_type.value,
            area,
            coverage,
            "adaptive_shape"
        ))
        
        print(f"Strategy 1 (Adaptive): {shape_type.value}, area={area:.0f}, coverage={coverage:.1%}")
        
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
    
    # Strategy 2: Forced rectangle (rotated LIR)
    if try_multiple_strategies:
        try:
            rect_corners, angle, rect_area = lir_rotated_safe(
                grid,
                angle_step=angle_step
            )
            
            coverage = compute_coverage(rect_area, field_area)
            
            results.append(InscribedResult(
                rect_corners,
                "rectangle",
                rect_area,
                coverage,
                "forced_rectangle"
            ))
            
            print(f"Strategy 2 (Rectangle): area={rect_area:.0f}, coverage={coverage:.1%}, angle={angle:.1f}°")
            
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
    
    # Select best result
    if not results:
        return InscribedResult(
            np.zeros((4, 2)), "failed", 0.0, 0.0, "none"
        )
    
    # Sort by area (descending)
    results.sort(key=lambda r: r.area, reverse=True)
    
    best = results[0]
    print(f"\n✅ Best strategy: {best.strategy} ({best.shape_type})")
    print(f"   Area: {best.area:.0f}, Coverage: {best.coverage:.1%}")
    
    return best


def generate_work_paths(inscribed_polygon: np.ndarray,
                       work_width: float = 20.0,
                       shape_type: str = "rectangle") -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate parallel work paths for agricultural operations.
    
    Args:
        inscribed_polygon: Vertices of work area
        work_width: Width of each work pass (pixels or meters)
        shape_type: Type of shape (affects path generation)
    
    Returns:
        List of (start_point, end_point) tuples for each path
    """
    n = len(inscribed_polygon)
    
    if n < 3:
        return []
    
    paths = []
    
    if shape_type in ["rectangle", "parallelogram"]:
        # For rectangles and parallelograms: parallel paths along longer edge
        edges = []
        for i in range(n):
            v = inscribed_polygon[(i + 1) % n] - inscribed_polygon[i]
            length = np.linalg.norm(v)
            edges.append((length, v, inscribed_polygon[i]))
        
        # Sort by length
        edges.sort(key=lambda x: x[0], reverse=True)
        
        # Longest edge is work direction
        _, direction_vec, start_corner = edges[0]
        direction = direction_vec / (np.linalg.norm(direction_vec) + 1e-10)
        
        # Perpendicular direction
        perpendicular = np.array([-direction[1], direction[0]])
        
        # Find width
        width = edges[1][0] if len(edges) > 1 else 100
        
        # Generate paths
        num_paths = int(width / work_width) + 1
        
        for i in range(num_paths):
            offset = perpendicular * (i * work_width)
            p1 = start_corner + offset
            p2 = p1 + direction * edges[0][0]
            paths.append((p1, p2))
    
    elif shape_type == "trapezoid":
        # For trapezoids: parallel paths between parallel edges
        # Find parallel edges
        edges = []
        for i in range(4):
            v = inscribed_polygon[(i + 1) % 4] - inscribed_polygon[i]
            edges.append((v, inscribed_polygon[i]))
        
        # Simplified: use first edge as direction
        direction = edges[0][0] / (np.linalg.norm(edges[0][0]) + 1e-10)
        perpendicular = np.array([-direction[1], direction[0]])
        
        # Estimate height
        height = 100  # Simplified
        num_paths = int(height / work_width) + 1
        
        for i in range(num_paths):
            # Interpolate between top and bottom edges
            t = i / max(num_paths - 1, 1)
            p1 = inscribed_polygon[0] * (1 - t) + inscribed_polygon[3] * t
            p2 = inscribed_polygon[1] * (1 - t) + inscribed_polygon[2] * t
            paths.append((p1, p2))
    
    elif shape_type == "triangle":
        # For triangles: converging paths
        # Use longest edge as base
        edges = []
        for i in range(3):
            v = inscribed_polygon[(i + 1) % 3] - inscribed_polygon[i]
            length = np.linalg.norm(v)
            edges.append((length, i))
        
        edges.sort(key=lambda x: x[0], reverse=True)
        base_idx = edges[0][1]
        
        base_start = inscribed_polygon[base_idx]
        base_end = inscribed_polygon[(base_idx + 1) % 3]
        apex = inscribed_polygon[(base_idx + 2) % 3]
        
        # Generate converging paths
        num_paths = int(edges[0][0] / work_width) + 1
        
        for i in range(num_paths):
            t = i / max(num_paths - 1, 1)
            # Interpolate from base to apex
            p1 = base_start * (1 - t) + apex * t
            p2 = base_end * (1 - t) + apex * t
            paths.append((p1, p2))
    
    return paths




def smart_inscribe_from_vertices(vertices: np.ndarray,
                                 angle_step: float = 1.0,
                                 try_multiple_strategies: bool = True,
                                 grid_resolution: int = 1000) -> InscribedResult:
    """
    Smart inscribed polygon directly from field boundary vertices.
    
    This is the recommended function for agricultural applications where
    field boundaries are defined by GPS coordinates.
    
    Args:
        vertices: Nx2 array of field boundary vertices (e.g., GPS coordinates)
        angle_step: Angle step for rectangle search (degrees)
        try_multiple_strategies: If True, try multiple strategies and pick best
        grid_resolution: Internal grid resolution for computation
    
    Returns:
        InscribedResult with best inscribed polygon
    
    Example:
        >>> # Field boundary from GPS
        >>> vertices = np.array([
        ...     [100, 200],  # Corner 1
        ...     [500, 250],  # Corner 2
        ...     [480, 600],  # Corner 3
        ...     [120, 550]   # Corner 4
        ... ])
        >>> 
        >>> result = smart_inscribe_from_vertices(vertices)
        >>> print(f"Shape: {result.shape_type}")
        >>> print(f"Coverage: {result.coverage:.1%}")
        >>> print(f"Work area vertices:\n{result.polygon}")
    """
    from .adaptive_shape import classify_shape
    
    # Validate input
    if len(vertices) < 3:
        raise ValueError("At least 3 vertices required")
    
    vertices = np.array(vertices, dtype=np.float64)
    
    # Step 1: Classify shape directly from vertices
    shape_type = classify_shape(vertices, angle_tolerance=5.0)
    print(f"Detected field shape: {shape_type.value} ({len(vertices)} vertices)")
    
    # Step 2: Create internal grid representation
    # Find bounding box
    min_x, min_y = vertices.min(axis=0)
    max_x, max_y = vertices.max(axis=0)
    
    # Add margin
    margin = 50
    min_x -= margin
    min_y -= margin
    max_x += margin
    max_y += margin
    
    # Calculate scale to fit in grid_resolution
    width = max_x - min_x
    height = max_y - min_y
    scale = grid_resolution / max(width, height)
    
    # Scale vertices to grid
    scaled_vertices = (vertices - np.array([min_x, min_y])) * scale
    
    # Create grid
    grid_size = int(max(width, height) * scale) + 100
    grid = np.zeros((grid_size, grid_size), dtype=np.uint8)
    
    # Fill polygon
    cv2.fillPoly(grid, [scaled_vertices.astype(np.int32)], 255)
    grid = grid > 0
    
    # Step 3: Compute inscribed polygon
    result = smart_inscribe(grid, angle_step, try_multiple_strategies)
    
    # Step 4: Scale back to original coordinates
    if result.area > 0:
        result.polygon = result.polygon / scale + np.array([min_x, min_y])
        result.area = result.area / (scale * scale)
    
    # Step 5: Compute actual coverage
    field_area = cv2.contourArea(vertices.astype(np.float32))
    result.coverage = result.area / field_area if field_area > 0 else 0.0
    
    return result


def smart_inscribe_from_gps(gps_coords: List[Tuple[float, float]],
                            angle_step: float = 1.0,
                            coordinate_system: str = "utm") -> InscribedResult:
    """
    Smart inscribed polygon from GPS coordinates.
    
    Args:
        gps_coords: List of (longitude, latitude) or (easting, northing) tuples
        angle_step: Angle step for rectangle search (degrees)
        coordinate_system: "wgs84" for lon/lat or "utm" for projected coordinates
    
    Returns:
        InscribedResult with best inscribed polygon in same coordinate system
    
    Example:
        >>> # Field boundary from GPS (UTM coordinates)
        >>> gps_coords = [
        ...     (500000, 4500000),  # Corner 1 (easting, northing)
        ...     (500100, 4500020),  # Corner 2
        ...     (500090, 4500150),  # Corner 3
        ...     (500010, 4500130)   # Corner 4
        ... ]
        >>> 
        >>> result = smart_inscribe_from_gps(gps_coords, coordinate_system="utm")
        >>> print(f"Work area: {result.area:.0f} square meters")
    """
    vertices = np.array(gps_coords, dtype=np.float64)
    
    if coordinate_system.lower() == "wgs84":
        # For WGS84 (lon/lat), we should project to a local coordinate system
        # For simplicity, we'll use a local approximation
        # In production, use proper projection (e.g., pyproj)
        print("Warning: WGS84 coordinates should be projected to UTM for accurate area calculation")
        
        # Simple local projection (not accurate for large areas)
        center = vertices.mean(axis=0)
        lat_scale = 111320  # meters per degree latitude
        lon_scale = 111320 * np.cos(np.radians(center[1]))  # meters per degree longitude
        
        vertices_projected = vertices.copy()
        vertices_projected[:, 0] = (vertices[:, 0] - center[0]) * lon_scale
        vertices_projected[:, 1] = (vertices[:, 1] - center[1]) * lat_scale
        
        result = smart_inscribe_from_vertices(vertices_projected, angle_step)
        
        # Project back to WGS84
        if result.area > 0:
            result.polygon[:, 0] = result.polygon[:, 0] / lon_scale + center[0]
            result.polygon[:, 1] = result.polygon[:, 1] / lat_scale + center[1]
    
    else:  # UTM or other projected coordinate system
        result = smart_inscribe_from_vertices(vertices, angle_step)
    
    return result

