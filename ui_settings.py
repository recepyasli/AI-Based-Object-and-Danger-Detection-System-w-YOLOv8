import FreeSimpleGUI as sg
from config import load_user_settings, save_user_settings
from video_utils import list_cameras
from zone_calibrator import launch_zone_calibrator

camera_devices = list_cameras()
camera_options = [[i,name] for i, name in enumerate(camera_devices)]
camera_names = [name for i, name in camera_options]

def launch_settings_window():
    cfg = load_user_settings()

    window_padding_x = 40
    layout = [
        [sg.VPush()],
        [
            sg.Push(),
            sg.Text('Araç Ayarları', font=('Segoe UI', 32), pad=(window_padding_x, window_padding_x)),
            sg.Push(),
        ],

        [
            sg.Text('Kamera Seç:', size=(33, 1), justification='right'),
            sg.Combo(camera_names, readonly=True, default_value=cfg.get("camera_name"), key="camera_name", size=(40, 1))
        ],
        [
            sg.Text('Alarm Ses Seviyesi (0-1):', size=(33, 1), justification='right'),
            sg.Slider(range=(0, 1), resolution=0.01, orientation='h', default_value=cfg["alarm_volume"],
                      key='alarm_volume', size=(40, 15))],
        [
            sg.Text("Alarmı Etkinleştir", size=(33, 1), justification='right'),
            sg.Checkbox("", default=cfg["alarm_enabled"], key='alarm_enabled')
        ],
        [
            sg.Text("Hata Ayıklama Çizimlerini Etkinleştir", size=(33, 1),justification='right'),
            sg.Checkbox("", default=cfg["debug_draw"], key='debug_draw', size=(15, 15))
        ],
        [
            sg.Text("Loglamayı Etkinleştir", size=(33, 1),justification='right'),
            sg.Checkbox("", default=cfg["enable_log"], key='enable_log', size=(15, 15))
        ],
        [
            sg.Text("Frame Bazında Görüntülemeyi Etkinleştir", size=(33, 1),justification='right'),
            sg.Checkbox("", default=cfg["enable_fbf"], key='enable_fbf', size=(15, 15))
        ],
        [
            sg.Push(),
            sg.Button('İptal', button_color=("#FFFFFF","#B10F2E")),
            sg.Button('Kaydet'),
            sg.Push(),
            sg.Button("Araç ve Çarpışma Bölgesini Ayarla"),
            sg.Push(),
        ],
        [sg.VPush()],
    ]

    window = sg.Window('Ayarlar', layout, size=(1280, 720), element_padding=(window_padding_x,0))
    while True:
        event, values = window.read()
        if event == 'Kaydet':
            camera_index = -1
            camera_name = values["camera_name"]

            for i, name in camera_options:
                if name == camera_name:
                    camera_index = i

            if camera_index == -1:
                continue

            cfg.update({
                "alarm_volume": float(values['alarm_volume']),
                "debug_draw": values['debug_draw'],
                "enable_log": values['enable_log'],
                "alarm_enabled": values['alarm_enabled'],
                "camera_name": camera_name,
                "camera_index": camera_index,
                "enable_fbf": values['enable_fbf'],
            })
            save_user_settings(cfg)
            break
        elif event == "Araç ve Çarpışma Bölgesini Ayarla":

            window.close()
            launch_zone_calibrator()
            launch_settings_window()

            cfg = load_user_settings()
        elif event in (sg.WIN_CLOSED, 'İptal'):
            break
    window.close()