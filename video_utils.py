import cv2
from pygrabber.dshow_graph import FilterGraph

def list_cameras(max_devices=10):
    graph = FilterGraph()
    devices = graph.get_input_devices()
    return devices

list_cameras()