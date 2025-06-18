import cv2
import numpy as np
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, simpledialog
from PIL import Image, ImageTk
import threading
import queue
import logging
import json
import os

class FeedbackCollector:
    def __init__(self):
        self.feedback_queue = queue.Queue()
        self.last_feedback_time = datetime.now()
        self.feedback_interval = timedelta(seconds=30)
        self.low_conf_threshold = 0.9
        self.feedback_window = None
        self.current_detections = []
        self.tracked_boxes = {}  
        self.last_frame = None  
        
        
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'feedback_collector.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('FeedbackCollector')
        self.logger.info("FeedbackCollector initialized")
        
    def check_detection(self, frame, detections, tracked_boxes=None):
        """Check detections and collect feedback for low confidence ones"""
        current_time = datetime.now()
        self.last_frame = frame.copy()  
        
       
        if tracked_boxes:
            self.tracked_boxes = tracked_boxes
        
        
        if current_time - self.last_feedback_time >= self.feedback_interval:
            self.logger.info("Checking for low confidence detections")
            self._process_low_conf_detections(frame, detections)
            self.last_feedback_time = current_time
            
    def _process_low_conf_detections(self, frame, detections):
        """Process detections with low confidence"""
        low_conf_detections = []
        
        for det in detections:
            try:
                conf = det.conf.cpu().numpy()[0]
                if conf < self.low_conf_threshold:
                    x1, y1, x2, y2 = det.xyxy[0].cpu().numpy()
                    cls = int(det.cls.cpu().numpy()[0])
                    track_id = getattr(det, 'track_id', None)
                    
                    
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                   
                    detection_region = frame[y1:y2, x1:x2]
                    
                  
                    tracking_info = None
                    if track_id and track_id in self.tracked_boxes:
                        tracking_info = self.tracked_boxes[track_id]
                    
                   
                    if (isinstance(detection_region, np.ndarray) and detection_region.size > 0 
                        and detection_region.shape[0] > 0 and detection_region.shape[1] > 0):
                     
                        detection_region = cv2.resize(detection_region, (128, 128), interpolation=cv2.INTER_AREA)
                        low_conf_detections.append({
                            'region': detection_region,
                            'confidence': conf,
                            'class': cls,
                            'bbox': (x1, y1, x2, y2),
                            'track_id': track_id,
                            'tracking_info': tracking_info,
                            'timestamp': datetime.now()
                        })
                        self.logger.info(f"Added low confidence detection: track_id={track_id}, conf={conf:.2f}")
            except Exception as e:
                self.logger.error(f"Error processing detection: {str(e)}")
                continue
        
        if low_conf_detections:
            self.logger.info(f"Found {len(low_conf_detections)} low confidence detections")
            self._show_feedback_window(frame, low_conf_detections)
        else:
            self.logger.info("No low confidence detections found")
            
    def _show_feedback_window(self, frame, detections):
        """Show feedback window for low confidence detections"""
        try:
            if self.feedback_window is not None:
                self.feedback_window.destroy()
                
            self.feedback_window = tk.Toplevel()
            self.feedback_window.title("Detection Feedback")
            self.feedback_window.geometry("1000x800")
            

            self.feedback_window.attributes('-topmost', True)
            self.feedback_window.transient(self.feedback_window.master)
            self.feedback_window.grab_set()
            
 
            main_canvas = tk.Canvas(self.feedback_window)
            scrollbar = ttk.Scrollbar(self.feedback_window, orient="vertical", command=main_canvas.yview)
            main_frame = ttk.Frame(main_canvas)
            
            main_canvas.configure(yscrollcommand=scrollbar.set)
            
            
            scrollbar.pack(side="right", fill="y")
            main_canvas.pack(side="left", fill="both", expand=True)
            
            
            main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
            
           
            title_label = ttk.Label(main_frame, 
                                  text="Please verify these detections",
                                  font=('Helvetica', 14, 'bold'))
            title_label.pack(pady=10)
            
            
            class_names = {
                0: 'pizza',
                1: 'box_open',
                2: 'box_close',
                3: 'box_nilon'
            }
            

            for i, det in enumerate(detections):
                det_frame = ttk.LabelFrame(main_frame, 
                                         text=f"Detection {i+1} ({class_names.get(det['class'], 'Unknown')} - Conf: {det['confidence']:.2f})")
                det_frame.pack(fill=tk.X, pady=5, padx=10)
                

                left_frame = ttk.Frame(det_frame)
                left_frame.pack(side=tk.LEFT, padx=5, pady=5)
                
                
                region = cv2.cvtColor(det['region'], cv2.COLOR_BGR2RGB)
                region = Image.fromarray(region)
                region = ImageTk.PhotoImage(region)
                
                
                img_label = ttk.Label(left_frame, image=region)
                img_label.image = region  
                img_label.pack(padx=5, pady=5)
                
                
                right_frame = ttk.Frame(det_frame)
                right_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
                
                
                info_text = f"Class: {class_names.get(det['class'], 'Unknown')}\n"
                info_text += f"Confidence: {det['confidence']:.2f}\n"
                if det['track_id'] is not None:
                    info_text += f"Track ID: {det['track_id']}\n"
                
                
                if det['tracking_info']:
                    track_info = det['tracking_info']
                    if 'status_history' in track_info:
                        status_text = "Status History: " + " -> ".join(
                            ["Open" if s == 1 else "Close" for s in track_info['status_history']]
                        )
                        info_text += status_text + "\n"
                    if 'in_dispatch_zone' in track_info:
                        info_text += f"In Zone: {track_info['in_dispatch_zone']}\n"
                
                ttk.Label(right_frame, text=info_text, wraplength=300).pack(pady=5)
                
                
                btn_frame = ttk.Frame(right_frame)
                btn_frame.pack(pady=10)
                
                ttk.Label(btn_frame, text="Is this detection correct?").pack(pady=5)
                
                def create_callback(det_idx, is_correct):
                    return lambda: self._submit_feedback(det_idx, is_correct, det)
                
                ttk.Button(btn_frame, text="Yes", 
                          command=create_callback(i, True)).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="No", 
                          command=create_callback(i, False)).pack(side=tk.LEFT, padx=5)
                
                
                options_frame = ttk.LabelFrame(right_frame, text="Additional Feedback")
                options_frame.pack(fill=tk.X, pady=5)
                
                
                issues = [
                    "Wrong class",
                    "Wrong position",
                    "Occluded",
                    "Poor lighting",
                    "Other"
                ]
                
                issue_vars = {}
                for issue in issues:
                    var = tk.BooleanVar()
                    issue_vars[issue] = var
                    ttk.Checkbutton(options_frame, text=issue, variable=var).pack(anchor=tk.W)
                
                
                det['issue_vars'] = issue_vars
            
            
            main_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
            
            
            close_btn = ttk.Button(main_frame, text="Close", command=self.feedback_window.destroy)
            close_btn.pack(pady=10)
            
            self.current_detections = detections
            self.logger.info("Feedback window created successfully")
            
            
            self.feedback_window.update_idletasks()
            width = self.feedback_window.winfo_width()
            height = self.feedback_window.winfo_height()
            x = (self.feedback_window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.feedback_window.winfo_screenheight() // 2) - (height // 2)
            self.feedback_window.geometry(f'{width}x{height}+{x}+{y}')
            
            
            now = datetime.now()
            db_dir = os.path.join('db', now.strftime('%Y%m%d'))
            os.makedirs(db_dir, exist_ok=True)
            unique_id = now.strftime('%H%M%S_%f')
            frame_filename = f"frame_{unique_id}.jpg"
            frame_path = os.path.join(db_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            for det in detections:
                det['original_frame'] = frame
                det['original_frame_path'] = frame_path
                det['frame_shape'] = frame.shape
                det['frame_filename'] = frame_filename
                det['db_dir'] = db_dir
            
        except Exception as e:
            self.logger.error(f"Error creating feedback window: {str(e)}")
            raise
            
    def _submit_feedback(self, det_idx, is_correct, detection):
        """Submit feedback for a detection"""
        try:
            
            issues = []
            if not is_correct and 'issue_vars' in detection:
                for issue, var in detection['issue_vars'].items():
                    if var.get():
                        issues.append(issue)

            
            should_save_for_training = (not is_correct) or (is_correct and detection['confidence'] < 0.7)
            if should_save_for_training:
                frame = detection.get('original_frame')
                frame_path = detection.get('original_frame_path')
                db_dir = detection.get('db_dir')
                frame_filename = detection.get('frame_filename')
                h, w = detection.get('frame_shape', (None, None))[0:2]
                x1, y1, x2, y2 = detection['bbox']
                
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = (x2 - x1) / w
                height = (y2 - y1) / h
                class_id = detection['class']
                
                if not is_correct:
                    root = self.feedback_window
                    new_class_id = simpledialog.askinteger(
                        "Re-identify Class",
                        "Enter correct class id (0: pizza, 1: box_open, 2: box_close, 3: box_nilon):",
                        parent=root,
                        minvalue=0,
                        maxvalue=3
                    )
                    if new_class_id is not None:
                        class_id = new_class_id
                
                label_filename = os.path.splitext(frame_filename)[0] + '.txt'
                label_path = os.path.join(db_dir, label_filename)
                with open(label_path, 'w') as f:
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
                if not os.path.exists(frame_path):
                    cv2.imwrite(frame_path, frame)
            

            feedback_data = {
                'timestamp': datetime.now(),
                'detection': {
                    'bbox': detection['bbox'],
                    'class': detection['class'],
                    'confidence': detection['confidence'],
                    'track_id': detection['track_id']
                },
                'is_correct': is_correct,
                'issues': issues,
                'tracking_info': detection.get('tracking_info'),
                'user_feedback': True
            }
            self.feedback_queue.put(feedback_data)
            self.logger.info(f"Feedback submitted for detection {det_idx}: {'correct' if is_correct else 'incorrect'}")
            
            if self.feedback_window:
                for widget in self.feedback_window.winfo_children():
                    if isinstance(widget, ttk.LabelFrame) and widget.winfo_children():
                        btn_frame = widget.winfo_children()[1]  # Get button frame
                        for btn in btn_frame.winfo_children():
                            if isinstance(btn, ttk.Button):
                                btn.configure(state='disabled')
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {str(e)}")
                            
    def get_feedback_data(self):
        """Get collected feedback data"""
        feedback_data = []
        while not self.feedback_queue.empty():
            feedback_data.append(self.feedback_queue.get())
        return feedback_data 