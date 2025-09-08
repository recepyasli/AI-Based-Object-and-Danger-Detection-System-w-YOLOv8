import FreeSimpleGUI as sg
from detector import run_detection
from ui_settings import launch_settings_window

def launch_menu():
    sg.theme_add_new('CrashDetectorWAI', {
        'BACKGROUND': '#070029',
        'TEXT': '#FFFFFF',
        'INPUT': '#ffffff',
        'TEXT_INPUT': '#070029',
        'SCROLL': '#ffffff',
        'BUTTON': ('#070029', '#ffffff'),
        'PROGRESS': ('#ffffff', '#070029'),
        'BORDER': 1,
        'SLIDER_DEPTH': 0,
        'PROGRESS_DEPTH': 0
    })

    sg.theme('CrashDetectorWAI')
    sg.set_options(font=('Segoe UI', 20))

    button_width = 10
    button_height = int(button_width * (1 - 9/16))

    layout = [
        [sg.VPush()],
        [sg.Text('Yapay Zeka ile Nesne ve Tehlike Tespit Sistemi', pad=(0, 40), justification='center', expand_x=True, font=('Segoe UI', 32))],
        [
            sg.Push(),
            sg.Button('Başlat', size=(button_width, button_height)),
            sg.Button('Test Modu', size=(button_width, button_height)),
            sg.Button('Ayarlar', size=(button_width, button_height)),
            sg.Button('Çıkış', size=(button_width, button_height),button_color=("#FFFFFF", "#B10F2E")),
            sg.Push()
        ],
        [sg.VPush()],
    ]

    window = sg.Window('Ana Menü', layout, size=(1280, 720), element_justification='center')

    def get_start_frame():
        layout = [
            [sg.Text("Başlangıç karesi:", font=('Segoe UI', 16))],
            [sg.Input(default_text="0", key="frame", enable_events=True, justification='center')],
            [sg.Button("Tamam", bind_return_key=True), sg.Button("İptal")]
        ]

        window = sg.Window("Başlangıç Karesi", layout, modal=True)

        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "İptal"):
                window.close()
                return None
            if event == "Tamam":
                try:
                    val = int(values["frame"])
                    window.close()
                    return max(val, 0)
                except:
                    sg.popup_error("Lütfen geçerli bir sayı girin.")

    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, 'Çıkış'):
            break
        elif event == 'Başlat':
            window.close()
            run_detection(mode="live")
            launch_menu()
        elif event == 'Test Modu':
            video_path = sg.popup_get_file("Bir video seçin", file_types=(("MP4 files", "*.mp4"),))
            if video_path:
                start_frame = get_start_frame()
                if start_frame is not None:
                    window.close()
                    run_detection(mode="test", video_path=video_path, start_frame=start_frame)
                    launch_menu()
        elif event == 'Ayarlar':
            window.close()
            launch_settings_window()
            launch_menu()
            return

    window.close()
