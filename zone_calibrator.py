import cv2
import os
import FreeSimpleGUI as sg
from config import load_user_settings, save_user_settings
from video_utils import list_cameras
import PIL.Image
import io

def convert_cv_to_bytes(img):
    img = cv2.resize(img, (480, 270))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = PIL.Image.fromarray(img)
    with io.BytesIO() as output:
        img_pil.save(output, format="PNG")
        data = output.getvalue()
    return data

def launch_zone_calibrator():
    cfg = load_user_settings()
    camera_devices = list_cameras()
    camera_options = [f"Camera {i} - {name}" for i, name in enumerate(camera_devices)]

    layout = [
        [sg.VPush()],
        [sg.Text('Çarpışma Bölgesi Ayarları', pad=(0, 40), justification='center', expand_x=True, font=('Segoe UI', 32))],
        [sg.Text("Görüntü Kaynağını Seçin", pad=(0, 20), justification="center", expand_x=True)],
        [sg.Push(), sg.Button("Kameradan"), sg.Button("Dosyadan"), sg.Button("İptal"), sg.Push()],
        [sg.VPush()]
    ]

    window = sg.Window("Görüntü Seçimi", layout, size=(1280, 720))
    event, _ = window.read()
    window.close()

    source_frame = None

    if event == "Kameradan":

        camera_devices = list_cameras()
        camera_options = [[i, name] for i, name in enumerate(camera_devices)]
        camera_names = [name for i, name in camera_options]

        cam_layout = [
            [sg.VPush()],
            [
                sg.Push(),
                sg.Text('Kamera Seç:', size=(33, 1), justification='right'),
                sg.Combo(camera_names, readonly=True, default_value=cfg.get("camera_name"), key="camera_name", size=(40, 1)),
                sg.Push(),
            ],
            [
                sg.Push(),
                sg.Button("İptal"),
                sg.Button("Tamam"),
                sg.Push(),
            ],
            [sg.VPush()]
        ]
        cam_win = sg.Window("Kamera Seç", cam_layout, size=(1280, 720))
        cam_event, values = cam_win.read()
        cam_win.close()

        if cam_event == "Tamam" and values["camera_name"]:
            try:
                camera_index = 0
                camera_name = values["camera_name"]

                for i, name in camera_options:
                    if name == camera_name:
                        camera_index = i

                cap = cv2.VideoCapture(camera_index)
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    sg.popup_error("Kamera görüntüsü alınamadı.")
                    return
                source_frame = frame
            except Exception as e:
                sg.popup_error("Kamera seçerken hata oluştu: ", e)
                return
        else:
            return

    elif event == "Dosyadan":
        path = sg.popup_get_file(
            "Görsel veya Video Seç",
            file_types=(("Tüm Desteklenen", "*.jpg *.jpeg *.png *.mp4 *.avi"),
                        ("Görseller", "*.jpg *.jpeg *.png"),
                        ("Videolar", "*.mp4 *.avi"))
        )
        if not path:
            return

        ext = os.path.splitext(path)[-1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            frame = cv2.imread(path)
            if frame is None:
                sg.popup_error("Görsel okunamadı.")
                return
            source_frame = frame

        elif ext in ['.mp4', '.avi']:
            cap = cv2.VideoCapture(path)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                sg.popup_error("Video okunamadı.")
                return
            source_frame = frame
        else:
            sg.popup_error("Desteklenmeyen dosya türü.")
            return

    elif event in ("İptal", sg.WIN_CLOSED):
        return

    if source_frame is not None:
        calibrate_on_frame_gui(source_frame, cfg)


def calibrate_on_frame_gui(frame, cfg):
    h, w = frame.shape[:2]

    vy = cfg.get("vehicle_box_y_ratio", 0.3)
    crash_x = cfg.get("crash_zone_x_ratio", 0.5)
    crash_y = cfg.get("crash_zone_y_ratio", 0.7)

    layout = [
        [sg.VPush()],
        [
            sg.Push(),
            sg.Text("Canlı Önizleme"),
            sg.Push()
        ],
        [
            sg.Push(),
            sg.Image(key="preview", size=(854, 480)),
            sg.Push()
        ],
        [
            sg.Push(),
            sg.Text("Vehicle Y Ratio:", size=(30, 1), justification="right"),
            sg.Push(),
            sg.Slider((0.0, 1.0), vy, resolution=0.001, orientation="h", key="vehicle_box_y_ratio", size=(30, 15),),
            sg.Push(),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.Text("Crash Zone X Ratio:", size=(30, 1), justification="right"),
            sg.Push(),
            sg.Slider((0.1, 1.0), crash_x, resolution=0.001, orientation="h", key="crash_zone_x_ratio", size=(30, 15)),
            sg.Push(),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.Text("Crash Zone Y Ratio:", size=(30, 1), justification="right"),
            sg.Push(),
            sg.Slider((0.1, 1.0), crash_y, resolution=0.001, orientation="h", key="crash_zone_y_ratio", size=(30, 15)),
            sg.Push(),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.Push(),
            sg.Button("İptal"),
            sg.Button("Kaydet"),
            sg.Push(),
        ],
        [sg.VPush()],
    ]
    win = sg.Window("Crash Zone Ayarı", layout, finalize=True, size=(1280, 720))

    while True:
        event, values = win.read(timeout=50)
        if event in (sg.WIN_CLOSED, "İptal"):
            break
        elif event == "Kaydet":
            cfg["vehicle_box_y_ratio"] = round(float(values["vehicle_box_y_ratio"]), 3)
            cfg["crash_zone_x_ratio"] = round(float(values["crash_zone_x_ratio"]), 3)
            cfg["crash_zone_y_ratio"] = round(float(values["crash_zone_y_ratio"]), 3)

            save_user_settings(cfg)
            sg.popup("Ayarlar kaydedildi.")
            break

        # Güncel önizleme
        y = int( (1-values["vehicle_box_y_ratio"]) * h)
        cx = float(values["crash_zone_x_ratio"])
        cy = float(values["crash_zone_y_ratio"])

        preview = frame.copy()
        cv2.rectangle(preview, (0, y), (w, h), (0, 255, 0), 2)
        crash_w = int(w * cx)
        crash_h = float((h - y) * cy)
        cx1 = int((w - crash_w) // 2)
        cx2 = int(cx1 + crash_w)
        cy1 = int(y + crash_h)
        cy2 = int(h)
        cv2.rectangle(preview, (cx1, cy1), (cx2, cy2), (0, 0, 255), 2)
        win["preview"].update(data=convert_cv_to_bytes(preview))

    win.close()