import math


def line_intersects_box(start_point, end_point, box):
    """
    FIXED: Check if a line segment intersects with a rectangular box.
    Uses proper line-box intersection algorithm.
    """
    x1, y1 = start_point
    x2, y2 = end_point
    bx1, by1, bx2, by2 = box

    # Normalize box coordinates
    if bx1 > bx2:
        bx1, bx2 = bx2, bx1
    if by1 > by2:
        by1, by2 = by2, by1

    # Check if line is completely outside box
    if (x1 < bx1 and x2 < bx1) or (x1 > bx2 and x2 > bx2):
        return False
    if (y1 < by1 and y2 < by1) or (y1 > by2 and y2 > by2):
        return False

    # Check if either endpoint is inside box
    if (bx1 <= x1 <= bx2 and by1 <= y1 <= by2) or (bx1 <= x2 <= bx2 and by1 <= y2 <= by2):
        return True

    # Check intersection with each box edge
    box_edges = [
        ((bx1, by1), (bx2, by1)),  # Top edge
        ((bx2, by1), (bx2, by2)),  # Right edge
        ((bx2, by2), (bx1, by2)),  # Bottom edge
        ((bx1, by2), (bx1, by1))  # Left edge
    ]

    for edge_start, edge_end in box_edges:
        if line_segments_intersect(start_point, end_point, edge_start, edge_end):
            return True

    return False


def line_segments_intersect(p1, p2, p3, p4):
    """
    FIXED: Proper line segment intersection using cross products.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    def cross_product(a, b, c):
        return (c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])

    d1 = cross_product(p3, p4, p1)
    d2 = cross_product(p3, p4, p2)
    d3 = cross_product(p1, p2, p3)
    d4 = cross_product(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    # Check for collinear points
    if d1 == 0 and point_on_segment(p3, p1, p4):
        return True
    if d2 == 0 and point_on_segment(p3, p2, p4):
        return True
    if d3 == 0 and point_on_segment(p1, p3, p2):
        return True
    if d4 == 0 and point_on_segment(p1, p4, p2):
        return True

    return False


def point_on_segment(p, q, r):
    """Check if point q lies on segment pr"""
    return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
            min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))


def point_in_box(point, box):
    """Check if point is inside box"""
    x, y = point
    x1, y1, x2, y2 = box
    return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)


def get_predicted_vectors(corners, motion_vectors, fps, seconds_to_predict):
    """
    FIXED: Calculate predicted positions based on motion vectors.
    """
    if fps <= 0:
        fps = 30  # Default fallback

    predicted_positions = []
    frames_to_predict = int(fps * seconds_to_predict)

    for corner, (dx, dy) in zip(corners, motion_vectors):
        # Calculate total displacement over the prediction time
        total_dx = dx * frames_to_predict
        total_dy = dy * frames_to_predict

        predicted_x = corner[0] + total_dx
        predicted_y = corner[1] + total_dy

        predicted_positions.append((predicted_x, predicted_y))

    return predicted_positions


def is_box_between_vectors(corner1, predicted1, corner2, predicted2, crash_box):
    """
    FIXED: Check if crash box intersects with the quadrilateral formed by two motion vectors.
    This checks if the object will "sweep" through the crash zone.
    """
    # Create quadrilateral from current positions and predicted positions
    quad = [corner1, corner2, predicted2, predicted1]

    # Get crash box corners
    bx1, by1, bx2, by2 = crash_box
    crash_corners = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2)]

    # Method 1: Check if any crash box corner is inside the motion quadrilateral
    for crash_corner in crash_corners:
        if point_in_polygon_winding(crash_corner, quad):
            return True

    # Method 2: Check if any quad corner is inside the crash box
    for quad_corner in quad:
        if point_in_box(quad_corner, crash_box):
            return True

    # Method 3: Check if any edges intersect
    quad_edges = [(quad[i], quad[(i + 1) % 4]) for i in range(4)]
    crash_edges = [
        ((bx1, by1), (bx2, by1)),  # Top
        ((bx2, by1), (bx2, by2)),  # Right
        ((bx2, by2), (bx1, by2)),  # Bottom
        ((bx1, by2), (bx1, by1))  # Left
    ]

    for quad_edge in quad_edges:
        for crash_edge in crash_edges:
            if line_segments_intersect(quad_edge[0], quad_edge[1], crash_edge[0], crash_edge[1]):
                return True

    return False


def point_in_polygon_winding(point, polygon):
    """
    FIXED: Winding number algorithm for point-in-polygon test.
    More robust than ray casting.
    """
    if len(polygon) < 3:
        return False

    x, y = point
    winding_number = 0

    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]

        if y1 <= y:
            if y2 > y:  # Upward crossing
                if is_left(polygon[i], polygon[(i + 1) % len(polygon)], point) > 0:
                    winding_number += 1
        else:
            if y2 <= y:  # Downward crossing
                if is_left(polygon[i], polygon[(i + 1) % len(polygon)], point) < 0:
                    winding_number -= 1

    return winding_number != 0


def is_left(p0, p1, p2):
    """Test if point p2 is left/on/right of line p0p1"""
    return ((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1]))


def getzones(frame_w, frame_h, y_ratio, cz_x_ratio, cz_y_ratio):
    """
    Calculate vehicle detection zone and crash zone coordinates.
    """
    # Vehicle detection zone (bottom portion of frame)
    vehicle_height = int(frame_h * y_ratio)
    vehicle_box = (0, frame_h - vehicle_height, frame_w, frame_h)

    # Crash zone (centered within vehicle zone)
    crash_width = int(frame_w * cz_x_ratio)
    crash_height = int(vehicle_height * cz_y_ratio)

    crash_x1 = (frame_w - crash_width) // 2
    crash_x2 = crash_x1 + crash_width
    crash_y1 = frame_h - crash_height
    crash_y2 = frame_h

    crash_box = (crash_x1, crash_y1, crash_x2, crash_y2)

    return vehicle_box, crash_box


def calculate_motion_vector(positions):
    """
    FIXED: Calculate average motion vector from position history.
    """
    if len(positions) < 2:
        return (0.0, 0.0)

    total_dx = 0.0
    total_dy = 0.0

    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        total_dx += dx
        total_dy += dy

    num_transitions = len(positions) - 1
    return (total_dx / num_transitions, total_dy / num_transitions)


def distance_point_to_line(point, line_start, line_end):
    """
    FIXED: Calculate perpendicular distance from point to line segment.
    """
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end

    # Calculate line length squared
    line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2

    if line_length_sq == 0:
        # Line is actually a point
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    # Calculate parameter t (projection of point onto line)
    t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq
    t = max(0, min(1, t))  # Clamp to [0,1] for line segment

    # Find closest point on line segment
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)

    # Return distance
    return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)