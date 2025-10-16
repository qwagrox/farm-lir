"""
Demonstration of non-axis-aligned (rotated) Largest Interior Rectangle.

This script shows the difference between axis-aligned and rotated LIR
on various shapes.
"""

import numpy as np
import cv2
import largestinteriorrectangle as lir


def draw_rectangle_corners(img, corners, color, thickness=2):
    """Draw a rectangle given its 4 corners."""
    corners_int = corners.astype(np.int32)
    cv2.polylines(img, [corners_int], True, color, thickness)
    
    # Draw corner points
    for corner in corners_int:
        cv2.circle(img, tuple(corner), 4, color, -1)


def create_diamond_shape(size=400):
    """Create a diamond-shaped binary mask."""
    img = np.zeros((size, size), dtype=np.uint8)
    center = size // 2
    pts = np.array([
        [center, 50],
        [size - 50, center],
        [center, size - 50],
        [50, center]
    ], np.int32)
    cv2.fillPoly(img, [pts], 255)
    return img > 0


def create_ellipse_shape(size=400):
    """Create an ellipse-shaped binary mask."""
    img = np.zeros((size, size), dtype=np.uint8)
    center = (size // 2, size // 2)
    axes = (size // 3, size // 4)
    cv2.ellipse(img, center, axes, 30, 0, 360, 255, -1)
    return img > 0


def create_irregular_polygon(size=400):
    """Create an irregular polygon."""
    img = np.zeros((size, size), dtype=np.uint8)
    pts = np.array([
        [100, 80],
        [300, 100],
        [350, 200],
        [320, 320],
        [200, 350],
        [80, 280],
        [60, 150]
    ], np.int32)
    cv2.fillPoly(img, [pts], 255)
    return img > 0


def demo_shape(grid, title, output_path):
    """
    Demonstrate both axis-aligned and rotated LIR on a shape.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {title}")
    print(f"{'='*60}")
    
    # Create visualization image
    h, w = grid.shape
    vis = np.zeros((h, w, 3), dtype=np.uint8)
    vis[grid] = [200, 200, 200]  # Gray background for the shape
    
    # Compute axis-aligned LIR
    print("Computing axis-aligned LIR...")
    rect_aligned = lir.lir(grid)
    x, y, width, height = rect_aligned
    area_aligned = width * height
    
    # Draw axis-aligned rectangle in blue
    pt1 = (x, y)
    pt2 = (x + width - 1, y + height - 1)
    cv2.rectangle(vis, pt1, pt2, (255, 0, 0), 2)
    
    print(f"  Axis-aligned LIR: {rect_aligned}")
    print(f"  Area: {area_aligned}")
    
    # Compute rotated LIR
    print("Computing rotated LIR (testing angles 0-180° with 1° step)...")
    corners_rotated, angle, area_rotated = lir.lir_rotated(
        grid, 
        angle_start=0, 
        angle_end=180, 
        angle_step=1.0
    )
    
    # Draw rotated rectangle in red
    draw_rectangle_corners(vis, corners_rotated, (0, 0, 255), 2)
    
    print(f"  Rotated LIR angle: {angle:.1f}°")
    print(f"  Area: {area_rotated:.1f}")
    
    # Calculate improvement
    improvement = ((area_rotated - area_aligned) / area_aligned) * 100
    print(f"  Improvement: {improvement:.1f}%")
    
    # Add text annotations
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(vis, title, (10, 30), font, 0.8, (255, 255, 255), 2)
    cv2.putText(vis, f"Axis-aligned (blue): {area_aligned}", 
                (10, h - 60), font, 0.5, (255, 0, 0), 1)
    cv2.putText(vis, f"Rotated (red): {area_rotated:.0f} at {angle:.1f}deg", 
                (10, h - 35), font, 0.5, (0, 0, 255), 1)
    cv2.putText(vis, f"Improvement: {improvement:.1f}%", 
                (10, h - 10), font, 0.5, (0, 255, 0), 1)
    
    # Save the result
    cv2.imwrite(output_path, vis)
    print(f"  Saved visualization to: {output_path}")
    
    return area_aligned, area_rotated, improvement


def main():
    """Run demonstrations on various shapes."""
    print("\n" + "="*60)
    print("Non-Axis-Aligned LIR Demonstration")
    print("="*60)
    print("\nThis demo compares axis-aligned LIR (blue) with")
    print("rotated LIR (red) on different shapes.")
    
    # Create output directory
    import os
    output_dir = "/home/ubuntu/lir_demo_output"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    # Demo 1: Diamond shape
    grid1 = create_diamond_shape(400)
    r1 = demo_shape(grid1, "Diamond Shape", 
                    os.path.join(output_dir, "demo_diamond.png"))
    results.append(("Diamond", *r1))
    
    # Demo 2: Ellipse
    grid2 = create_ellipse_shape(400)
    r2 = demo_shape(grid2, "Rotated Ellipse", 
                    os.path.join(output_dir, "demo_ellipse.png"))
    results.append(("Ellipse", *r2))
    
    # Demo 3: Irregular polygon
    grid3 = create_irregular_polygon(400)
    r3 = demo_shape(grid3, "Irregular Polygon", 
                    os.path.join(output_dir, "demo_polygon.png"))
    results.append(("Polygon", *r3))
    
    # Demo 4: Small test grid
    grid4 = np.array([
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
    ], dtype=bool)
    
    # Scale up for better visualization
    grid4_scaled = np.repeat(np.repeat(grid4, 50, axis=0), 50, axis=1)
    r4 = demo_shape(grid4_scaled, "Small Test Grid (50x scaled)", 
                    os.path.join(output_dir, "demo_grid.png"))
    results.append(("Grid", *r4))
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Shape':<20} {'Aligned':<12} {'Rotated':<12} {'Improvement':<12}")
    print("-"*60)
    for name, area_aligned, area_rotated, improvement in results:
        print(f"{name:<20} {area_aligned:<12.0f} {area_rotated:<12.0f} {improvement:<12.1f}%")
    
    print("\n" + "="*60)
    print(f"All visualizations saved to: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()

