from collections import deque


class TrackedObject:
    def __init__(self, obj_id, cls_name, history_length=150):
        """
        Initialize tracked object with 150 frame cap by default.

        Args:
            obj_id: unique object identifier
            cls_name: object class name (car, person, etc.)
            history_length: maximum number of frames to store (default 150)
        """
        self.id = obj_id
        self.cls_name = cls_name
        # Cap history at 150 frames max for memory efficiency
        self.boxes = deque(maxlen=min(history_length, 150))

    def add(self, box):
        """Add new bounding box to history"""
        self.boxes.append(box)

    def get_last_n_boxes(self, n):
        """Get last n boxes from history"""
        if n <= 0:
            return []
        return list(self.boxes)[-n:]

    def get_corner_motion_vectors(self, n):
        """
        Calculate motion vectors for each corner over last n frames.

        Args:
            n: number of frames to analyze

        Returns:
            List of (dx, dy) tuples for each corner [TL, TR, BL, BR]
        """
        boxes = self.get_last_n_boxes(n)
        if len(boxes) < 2:
            return [(0.0, 0.0)] * 4

        # Extract corners for each frame: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        corners_history = []
        for (x1, y1, x2, y2) in boxes:
            corners_history.append([
                (x1, y1),  # 0: Top-Left
                (x2, y1),  # 1: Top-Right
                (x1, y2),  # 2: Bottom-Left
                (x2, y2)  # 3: Bottom-Right
            ])

        # Calculate average motion vector for each corner
        vectors = []
        for corner_idx in range(4):
            total_dx = 0.0
            total_dy = 0.0

            # Sum up movement between consecutive frames
            for frame_idx in range(len(corners_history) - 1):
                current_corner = corners_history[frame_idx][corner_idx]
                next_corner = corners_history[frame_idx + 1][corner_idx]

                dx = next_corner[0] - current_corner[0]
                dy = next_corner[1] - current_corner[1]

                total_dx += dx
                total_dy += dy

            # Calculate average motion per frame
            num_transitions = len(corners_history) - 1
            if num_transitions > 0:
                avg_dx = total_dx / num_transitions
                avg_dy = total_dy / num_transitions
            else:
                avg_dx = avg_dy = 0.0

            vectors.append((avg_dx, avg_dy))

        return vectors

    def get_total_frames(self):
        """Get total number of frames stored"""
        return len(self.boxes)

    def get_movement_magnitude(self, n=10):
        """
        Calculate total movement magnitude over last n frames.
        Useful for filtering out stationary objects.
        """
        if n <= 0 or len(self.boxes) < 2:
            return 0.0

        boxes = self.get_last_n_boxes(min(n, len(self.boxes)))
        if len(boxes) < 2:
            return 0.0

        total_movement = 0.0

        for i in range(1, len(boxes)):
            # Calculate center movement
            prev_center_x = (boxes[i - 1][0] + boxes[i - 1][2]) / 2
            prev_center_y = (boxes[i - 1][1] + boxes[i - 1][3]) / 2
            curr_center_x = (boxes[i][0] + boxes[i][2]) / 2
            curr_center_y = (boxes[i][1] + boxes[i][3]) / 2

            dx = curr_center_x - prev_center_x
            dy = curr_center_y - prev_center_y

            movement = (dx * dx + dy * dy) ** 0.5
            total_movement += movement

        return total_movement