import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import cv2
from datetime import datetime
import threading
import queue

class VideoProcessorGUI:
    def __init__(self, root, detection_handler):
        self.root = root
        self.root.title("YOLO Video Detection")
        self.root.geometry("1200x800")
        
     
        self.detection_handler = detection_handler
        
       
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
       
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
      
        self.video_path = tk.StringVar()
        
       
        self.create_widgets()
        
       
        self.is_processing = False
        self.stop_event = threading.Event()
        
     
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
       
        self.log_queue = queue.Queue()
        self.process_log_queue()
        
    def create_widgets(self):
      
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
       
        file_frame = ttk.LabelFrame(control_frame, text="Video Selection", padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
      
        self.path_entry = ttk.Entry(file_frame, textvariable=self.video_path, width=50)
        self.path_entry.grid(row=0, column=0, padx=5, pady=5)
        
     
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=1, padx=5, pady=5)
        
    
        zone_select_frame = ttk.LabelFrame(control_frame, text="Dispatch Zone Selection", padding="5")
        zone_select_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
      
        self.zone_buttons = {}
        for zone_id in self.detection_handler.get_available_zones():
            zone_info = self.detection_handler.get_zone_info(zone_id)
            btn = ttk.Button(zone_select_frame, 
                           text=f"Zone {zone_id}",
                           command=lambda zid=zone_id: self.select_zone(zid))
            btn.grid(row=0, column=zone_id-1, padx=5, pady=5)
            self.zone_buttons[zone_id] = btn
        

        self.process_btn = ttk.Button(control_frame, text="Start Processing", command=self.toggle_processing)
        self.process_btn.grid(row=2, column=0, pady=20)
        
 
        self.status_label = ttk.Label(control_frame, text="Status: Ready")
        self.status_label.grid(row=3, column=0, pady=5)
        
    
        stats_frame = ttk.LabelFrame(control_frame, text="Box Statistics", padding="5")
        stats_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
    
        self.pending_label = ttk.Label(stats_frame, text="Pending Boxes: 0")
        self.pending_label.grid(row=0, column=0, pady=2)
        
    
        self.sold_label = ttk.Label(stats_frame, text="Boxes Sold: 0")
        self.sold_label.grid(row=1, column=0, pady=2)
  

        zone_frame = ttk.LabelFrame(control_frame, text="Dispatch Zone Info", padding="5")
        zone_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        

        total_area = self.detection_handler.dispatch_zone.get_area_size()
        ttk.Label(zone_frame, text=f"Total Area: {total_area:.2f} pixels²").grid(row=0, column=0, pady=2)
        
   
        sub_areas = self.detection_handler.dispatch_zone.get_sub_area_sizes()
        for i, area in enumerate(sub_areas):
            ttk.Label(zone_frame, text=f"Area {i+1}: {area:.2f} pixels²").grid(row=i+1, column=0, pady=2)
        
 
        log_frame = ttk.LabelFrame(control_frame, text="Detection Log", padding="5")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.grid(row=0, column=0, padx=5, pady=5)
        

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        

        self.video_frame = ttk.LabelFrame(self.main_frame, text="Video Display", padding="5")
        self.video_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
   
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        

        self.update_zone_buttons()
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(
                ("Video files", "*.mp4 *.avi *.mov"),
                ("All files", "*.*")
            )
        )
        if filename:
            self.video_path.set(filename)
            
    def log_message(self, message):
        self.log_queue.put(message)
        
    def update_video_frame(self, frame):

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (1024, 768))  
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)

        self.video_label.configure(image=photo)
        self.video_label.image = photo 
        
    def toggle_processing(self):
        if not self.is_processing:
            if not self.video_path.get():
                messagebox.showerror("Error", "Please select a video file first!")
                return
            self.is_processing = True
            self.stop_event.clear()
            self.process_btn.configure(text="Stop Processing")
            self.status_label.configure(text="Status: Processing...")
  
            self.processing_thread = threading.Thread(target=self.detection_handler.process_video, 
                                                    args=(self.video_path.get(), self, self.stop_event))
            self.processing_thread.start()
        else:
            self.is_processing = False
            self.stop_event.set()
            self.process_btn.configure(text="Start Processing")
            self.status_label.configure(text="Status: Stopping...")

            if hasattr(self, 'processing_thread'):
                self.processing_thread.join(timeout=2.0)
            self.status_label.configure(text="Status: Stopped")

    def process_log_queue(self):
        """Process log messages from the queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def reset_gui_state(self):
        self.is_processing = False
        self.process_btn.configure(text="Start Processing")
        self.status_label.configure(text="Status: Ready")
        messagebox.showinfo("Complete", "Video processing completed!")

    def update_counts(self, pending_count, sold_count):
        """Update the box count displays in the GUI"""
        self.pending_label.configure(text=f"Pending Boxes: {pending_count}")
        self.sold_label.configure(text=f"Boxes Sold: {sold_count}")

    def select_zone(self, zone_id):
        """Select a dispatch zone"""
        if self.detection_handler.set_active_zone(zone_id):
            self.log_message(f"Selected Zone {zone_id}")
            self.update_zone_buttons()

            zone_info = self.detection_handler.get_zone_info(zone_id)
            if zone_info:
                total_area = self.detection_handler.dispatch_zone.get_area_size()
                sub_areas = self.detection_handler.dispatch_zone.get_sub_area_sizes()

                for widget in self.video_frame.master.grid_slaves():
                    if isinstance(widget, ttk.LabelFrame) and widget.cget('text') == "Dispatch Zone Info":
                        for child in widget.grid_slaves():
                            child.destroy()
                        ttk.Label(widget, text=f"Total Area: {total_area:.2f} pixels²").grid(row=0, column=0, pady=2)
                        for i, area in enumerate(sub_areas):
                            ttk.Label(widget, text=f"Area {i+1}: {area:.2f} pixels²").grid(row=i+1, column=0, pady=2)
    
    def update_zone_buttons(self):
        """Update the state of zone selection buttons"""
        active_zone = self.detection_handler.active_zone_id
        for zone_id, btn in self.zone_buttons.items():
            if zone_id == active_zone:
                btn.configure(style='Accent.TButton')
            else:
                btn.configure(style='TButton') 