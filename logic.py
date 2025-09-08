from geometry import line_intersects_box, get_predicted_vectors, is_box_between_vectors
import math


def is_dangerous(obj, fps, crash_box, config):
    """
    COMPLETELY REWRITTEN: Proper danger detection logic.

    Only checks:
    1. If any corner vector intersects crash zone
    2. If crash zone is between adjacent corner vectors (sweep detection)
    """
    # Get required frames for tracking
    required_frames = config.get("position_history_frames", 6)

    # Basic validation
    if len(obj.boxes) < required_frames:
        return False, "insufficient_history"

    if obj.cls_name not in config.get("critical_objects", []):
        return False, "not_critical_object"

    # Get recent position data
    recent_boxes = obj.get_last_n_boxes(required_frames)
    if not recent_boxes:
        return False, "no_recent_boxes"

    # Get current bounding box corners
    current_box = recent_boxes[-1]
    x1, y1, x2, y2 = current_box

    # Define corners: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    corners = [
        (x1, y1),  # 0: Top-Left
        (x2, y1),  # 1: Top-Right
        (x1, y2),  # 2: Bottom-Left
        (x2, y2)  # 3: Bottom-Right
    ]

    # Get motion vectors for each corner
    motion_vectors = obj.get_corner_motion_vectors(required_frames)
    if not motion_vectors or len(motion_vectors) != 4:
        return False, "invalid_motion_vectors"

    # Check if object is moving enough to matter
    movement_threshold = config.get("movement_threshold", 1.0)  # Lowered threshold
    total_movement = sum(math.sqrt(dx * dx + dy * dy) for dx, dy in motion_vectors)

    if total_movement < movement_threshold:
        return False, "insufficient_movement"

    # Calculate predicted positions
    seconds_to_predict = config.get("seconds_to_predict", 3.0)

    try:
        predicted_positions = get_predicted_vectors(corners, motion_vectors, fps, seconds_to_predict)
    except Exception as e:
        return False, f"prediction_error: {e}"

    if len(predicted_positions) != 4:
        return False, "invalid_predictions"

    # TEST 1: Check if any corner trajectory hits crash zone
    corner_names = ["TL", "TR", "BL", "BR"]
    for i, (current, predicted) in enumerate(zip(corners, predicted_positions)):
        if line_intersects_box(current, predicted, crash_box):
            return True, f"vector_hit_{corner_names[i]}_corner"

    # TEST 2: Check if crash zone is between adjacent corner vectors (sweep detection)
    # Adjacent pairs form the edges of the bounding box
    adjacent_pairs = [
        (0, 1, "top_edge"),  # Top-Left to Top-Right
        (1, 3, "right_edge"),  # Top-Right to Bottom-Right
        (3, 2, "bottom_edge"),  # Bottom-Right to Bottom-Left
        (2, 0, "left_edge")  # Bottom-Left to Top-Left
    ]

    for i, j, edge_name in adjacent_pairs:
        corner1 = corners[i]
        predicted1 = predicted_positions[i]
        corner2 = corners[j]
        predicted2 = predicted_positions[j]

        if is_box_between_vectors(corner1, predicted1, corner2, predicted2, crash_box):
            return True, f"sweep_through_{edge_name}"

    # TEST 3: Additional check - if object will completely contain crash zone
    # Check if crash zone will be inside the predicted bounding box
    pred_x1 = min(p[0] for p in predicted_positions)
    pred_y1 = min(p[1] for p in predicted_positions)
    pred_x2 = max(p[0] for p in predicted_positions)
    pred_y2 = max(p[1] for p in predicted_positions)

    crash_x1, crash_y1, crash_x2, crash_y2 = crash_box

    if (pred_x1 <= crash_x1 and pred_x2 >= crash_x2 and
            pred_y1 <= crash_y1 and pred_y2 >= crash_y2):
        return True, "object_will_contain_crash_zone"

    return False, "no_danger_detected"


def debug_danger_detection(obj, fps, crash_box, config):
    """
    Debug function to print detailed analysis of danger detection.
    Use this to troubleshoot why detection is/isn't working.
    """
    print(f"\n=== DEBUG DANGER DETECTION ===")
    print(f"Object ID: {obj.id}, Class: {obj.cls_name}")
    print(f"FPS: {fps}")
    print(f"Crash Box: {crash_box}")

    # Calculate dynamic required frames (5 seconds worth, capped at 150)
    if fps <= 0:
        fps = 30
    frames_for_5_seconds = int(fps * 5)
    required_frames = min(frames_for_5_seconds, 150)
    required_frames = max(required_frames, 10)

    print(f"Frames for 5 seconds: {frames_for_5_seconds}")
    print(f"Required frames (capped): {required_frames}, Available: {len(obj.boxes)}")

    if len(obj.boxes) < required_frames:
        print("❌ Not enough history")
        return

    recent_boxes = obj.get_last_n_boxes(required_frames)
    current_box = recent_boxes[-1]
    x1, y1, x2, y2 = current_box

    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    print(f"Current corners: {corners}")

    motion_vectors = obj.get_corner_motion_vectors(required_frames)
    print(f"Motion vectors: {motion_vectors}")

    total_movement = sum(math.sqrt(dx * dx + dy * dy) for dx, dy in motion_vectors)
    movement_threshold = config.get("movement_threshold", 1.0)
    print(f"Total movement: {total_movement}, Threshold: {movement_threshold}")

    if total_movement < movement_threshold:
        print("❌ Insufficient movement")
        return

    seconds_to_predict = config.get("seconds_to_predict", 3.0)
    predicted_positions = get_predicted_vectors(corners, motion_vectors, fps, seconds_to_predict)
    print(f"Predicted positions: {predicted_positions}")

    # Test each corner vector
    corner_names = ["TL", "TR", "BL", "BR"]
    for i, (current, predicted) in enumerate(zip(corners, predicted_positions)):
        intersects = line_intersects_box(current, predicted, crash_box)
        print(f"Corner {corner_names[i]}: {current} -> {predicted}, Hits crash: {intersects}")

    # Test sweep detection
    adjacent_pairs = [(0, 1, "top"), (1, 3, "right"), (3, 2, "bottom"), (2, 0, "left")]
    for i, j, edge_name in adjacent_pairs:
        sweeps = is_box_between_vectors(corners[i], predicted_positions[i],
                                        corners[j], predicted_positions[j], crash_box)
        print(f"Sweep {edge_name} edge: {sweeps}")

    print("=== END DEBUG ===\n")