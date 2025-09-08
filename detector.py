import cv2
import time

from sympy import false
from ultralytics import YOLO
from config import load_user_settings
from tracker import TrackedObject
from logic import is_dangerous
from geometry import getzones, get_predicted_vectors
from audio import play_alert
import logging

# Frame sabiti
MAX_W, MAX_H = 1280, 720
logging.getLogger('ultralytics').setLevel(logging.CRITICAL)

fps_perframe = {}
def run_detection(mode="test", video_path=None, start_frame=0):
    USER_SETTINGS = load_user_settings()
    LOGGING_ENABLED = USER_SETTINGS["enable_log"]
    ZONE_HISTORY_LENGTH = USER_SETTINGS["position_history_frames"]

    # Kamera/video kaynağı
    if mode == "test":
        if not video_path:
            video_path = "../../data/test/2.mp4"
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    else:
        cam_index = USER_SETTINGS.get("camera_index", 0)
        cap = cv2.VideoCapture(cam_index)

    model = YOLO("models/yolov8n.pt")
    tracked_objects = {}
    frame_count = 0
    vehicle_box, crash_box = None, None
    last_frame_time = time.time()
    fps = 0

    fbf_enabled = USER_SETTINGS.get("enable_fbf", False)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        current_time = time.time()
        fps = 1 / (current_time - last_frame_time + 1e-5)
        last_frame_time = current_time

        fps_perframe[frame_count] = fps

        fps_values = list(fps_perframe.values())
        average_fps = sum(fps_values) / len(fps_values)

        h, w = frame.shape[:2]
        if w > MAX_W or h > MAX_H:
            scale = min(MAX_W / w, MAX_H / h)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            h, w = frame.shape[:2]

        results = model.track(frame, persist=True)[0]
        frame_out = results.plot() if USER_SETTINGS["debug_draw"] else frame.copy()

        if crash_box is None:
            vehicle_box, crash_box = getzones(w, h, USER_SETTINGS["vehicle_box_y_ratio"],
                                              USER_SETTINGS.get("crash_zone_x_ratio"),
                                              USER_SETTINGS.get("crash_zone_y_ratio"))

        if USER_SETTINGS["debug_draw"]:
            cv2.rectangle(frame_out, (vehicle_box[0], vehicle_box[1]), (vehicle_box[2], vehicle_box[3]), (0, 255, 0), 2)
            cv2.rectangle(frame_out, (crash_box[0], crash_box[1]), (crash_box[2], crash_box[3]), (0, 0, 255), 2)

        cv2.putText(frame_out, f"FPS: {average_fps:.2f}", (frame_out.shape[1] - 150, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        current_ids = set()
        danger_detected = False

        for box in results.boxes:
            cls = int(box.cls[0])
            class_name = model.names[cls]
            obj_id = int(box.id[0]) if box.id is not None else None
            if obj_id is None or class_name not in USER_SETTINGS["critical_objects"]:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if obj_id not in tracked_objects:
                tracked_objects[obj_id] = TrackedObject(obj_id, class_name, ZONE_HISTORY_LENGTH)

            obj = tracked_objects[obj_id]
            obj.add((x1, y1, x2, y2))

            is_danger, reason = is_dangerous(obj, average_fps, crash_box, USER_SETTINGS)
            current_ids.add(obj_id)

            # Debug yön vektörleri çiz
            if USER_SETTINGS["debug_draw"] and len(obj.boxes) >= ZONE_HISTORY_LENGTH:
                last_box = obj.get_last_n_boxes(ZONE_HISTORY_LENGTH)[-1]
                corners = [(last_box[0], last_box[1]), (last_box[2], last_box[1]),
                           (last_box[0], last_box[3]), (last_box[2], last_box[3])]
                raw_vectors = obj.get_corner_motion_vectors(ZONE_HISTORY_LENGTH)

                predicted_vectors = get_predicted_vectors(corners, raw_vectors, average_fps, USER_SETTINGS["seconds_to_predict"])
                for corner, predicted in zip(corners, predicted_vectors):
                    cv2.arrowedLine(frame_out, corner, (int(predicted[0]), int(predicted[1])), (255, 0, 255), 2)

            if is_danger:
                cv2.rectangle(frame_out, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame_out, f"TEHLIKE: {class_name.upper()}!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                if USER_SETTINGS["alarm_enabled"]:
                    play_alert(USER_SETTINGS["alarm_path"],
                                       duration=2,
                                       volume=USER_SETTINGS["alarm_volume"])
                danger_detected = True
                if LOGGING_ENABLED:
                    print(f"Frame: {frame_count}")
                    print(f"⚠️ Alarm - ID: {obj_id}, Reason: {reason}")


        # Silinen objeleri temizle
        lost_ids = [oid for oid in tracked_objects if oid not in current_ids]
        for oid in lost_ids:
            del tracked_objects[oid]

        if not danger_detected:
            cv2.putText(frame_out, "Sistem Calisiyor - Tehlike Yok", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Yapay Zeka ile Nesne ve Tehlike Tespiti Sistemi", frame_out)

        if fbf_enabled:
            cv2.putText(frame_out, "Sonraki frame'e gecmek icin Enter'a basin",
                        (frame_out.shape[1] - 480, frame_out.shape[0] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            key = cv2.waitKey(0)
        else:
            key = cv2.waitKey(1)

        cv2.putText(frame_out, "Cikmak icin Q'ya basin", (frame_out.shape[1] - 350, frame_out.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        if key & 0xFF in [ord("q"), ord("Q")]:
            break
    cap.release()
    cv2.destroyAllWindows()
