from .lir import lir, pt1, pt2  # noqa: F401
from .lir_rotated import lir_rotated, largest_interior_rectangle_rotated  # noqa: F401
from .lir_contour_based import lir_contour_optimized, lir_hybrid, detect_polygon_angles  # noqa: F401
from .lir_geometric import lir_geometric, lir_geometric_from_polygon, lir_geometric_convex_hull  # noqa: F401
from .lir_safe import lir_safe  # noqa: F401
from .lir_rotated_safe import lir_rotated_safe  # noqa: F401
from .smart_inscribe import smart_inscribe, smart_inscribe_from_vertices, smart_inscribe_from_gps, generate_work_paths, InscribedResult  # noqa: F401
from .adaptive_shape import classify_shape, ShapeType  # noqa: F401

__version__ = "0.2.1"
