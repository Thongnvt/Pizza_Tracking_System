import tkinter as tk
from backend.utils.gui_handler import VideoProcessorGUI
from backend.utils.detection_handler import DetectionHandler

def main():
  
    root = tk.Tk()
    

    detection_handler = DetectionHandler()
    
  
    app = VideoProcessorGUI(root, detection_handler)
    

    root.mainloop()

if __name__ == "__main__":
    main() 