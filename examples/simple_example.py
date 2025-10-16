"""
Simple example of using non-axis-aligned LIR.
"""

import numpy as np
import cv2
import largestinteriorrectangle as lir


def example1_basic_usage():
    """Example 1: Basic usage with a diamond shape"""
    print("="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Create a diamond-shaped region
    grid = np.array([
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ], dtype=bool)
    
    print("Input grid:")
    print(grid.astype(int))
    
    # Compute axis-aligned LIR
    rect_aligned = lir.lir(grid)
    area_aligned = rect_aligned[2] * rect_aligned[3]
    print(f"\nAxis-aligned LIR: {rect_aligned}")
    print(f"Area: {area_aligned}")
    
    # Compute rotated LIR
    corners, angle, area = lir.lir_rotated(grid, angle_step=5.0)
    print(f"\nRotated LIR:")
    print(f"  Optimal angle: {angle}°")
    print(f"  Area: {area}")
    print(f"  Improvement: {(area - area_aligned) / area_aligned * 100:.1f}%")
    print(f"  Corners:\n{corners}")


def example2_return_formats():
    """Example 2: Different return formats"""
    print("\n" + "="*60)
    print("Example 2: Return Formats")
    print("="*60)
    
    grid = np.array([
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
    ], dtype=bool)
    
    # Format 1: Return corners (default)
    corners, angle, area = lir.lir_rotated(grid, return_corners=True, angle_step=10.0)
    print("Format 1 - Corners:")
    print(f"  Corners shape: {corners.shape}")
    print(f"  Angle: {angle}°")
    print(f"  Area: {area}")
    
    # Format 2: Return center, size, and angle
    result = lir.lir_rotated(grid, return_corners=False, angle_step=10.0)
    print("\nFormat 2 - Center/Size/Angle:")
    print(f"  Center: ({result[0]:.2f}, {result[1]:.2f})")
    print(f"  Size: {result[2]:.2f} x {result[3]:.2f}")
    print(f"  Angle: {result[4]:.1f}°")
    print(f"  Area: {result[5]:.2f}")


def example3_custom_angles():
    """Example 3: Custom angle range and step"""
    print("\n" + "="*60)
    print("Example 3: Custom Angle Range")
    print("="*60)
    
    grid = np.array([
        [0, 0, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 0, 0],
    ], dtype=bool)
    
    # Search only in 0-90 degrees with 5-degree step
    corners, angle, area = lir.lir_rotated(
        grid,
        angle_start=0.0,
        angle_end=90.0,
        angle_step=5.0
    )
    
    print(f"Angle range: [0°, 90°)")
    print(f"Angle step: 5°")
    print(f"Optimal angle: {angle}°")
    print(f"Area: {area}")


def example4_with_visualization():
    """Example 4: With visualization"""
    print("\n" + "="*60)
    print("Example 4: With Visualization")
    print("="*60)
    
    # Create a more interesting shape
    size = 200
    img = np.zeros((size, size), dtype=np.uint8)
    
    # Draw a rotated rectangle
    center = (size // 2, size // 2)
    axes = (60, 30)
    angle_draw = 25
    cv2.ellipse(img, center, axes, angle_draw, 0, 360, 255, -1)
    grid = img > 0
    
    # Compute both LIRs
    rect_aligned = lir.lir(grid)
    corners_rotated, angle, area_rotated = lir.lir_rotated(grid, angle_step=2.0)
    
    # Create visualization
    vis = np.zeros((size, size, 3), dtype=np.uint8)
    vis[grid] = [200, 200, 200]
    
    # Draw axis-aligned rectangle (blue)
    x, y, w, h = rect_aligned
    cv2.rectangle(vis, (x, y), (x + w - 1, y + h - 1), (255, 0, 0), 2)
    
    # Draw rotated rectangle (red)
    corners_int = corners_rotated.astype(np.int32)
    cv2.polylines(vis, [corners_int], True, (0, 0, 255), 2)
    
    # Save
    output_path = "/home/ubuntu/lir_demo_output/simple_example.png"
    cv2.imwrite(output_path, vis)
    
    area_aligned = rect_aligned[2] * rect_aligned[3]
    print(f"Axis-aligned area: {area_aligned}")
    print(f"Rotated area: {area_rotated:.0f}")
    print(f"Improvement: {(area_rotated - area_aligned) / area_aligned * 100:.1f}%")
    print(f"Visualization saved to: {output_path}")


def main():
    print("\n" + "="*60)
    print("Non-Axis-Aligned LIR - Simple Examples")
    print("="*60 + "\n")
    
    example1_basic_usage()
    example2_return_formats()
    example3_custom_angles()
    example4_with_visualization()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()

