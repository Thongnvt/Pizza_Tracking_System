import cv2
import torch
from ultralytics import YOLO
from datetime import datetime
from .dispatch_zone import DispatchZone
from .box_tracker import BoxTracker
from .feedback_collector import FeedbackCollector
from .feedback_storage import FeedbackStorage
from .import_helper import get_model_path, get_model_config_dict, get_full_model_config
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from SFSORT import SFSORT
import numpy as np
import logging

def compute_iou(boxA, boxB):
    
    boxA = np.array(boxA).astype(float).flatten()
    boxB = np.array(boxB).astype(float).flatten()
    assert boxA.shape == (4,) and boxB.shape == (4,)
    
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return float(iou)

class DetectionHandler:
    def __init__(self):
        # Get model configuration using flexible import
        self.model_config = get_full_model_config()
        self.model_path = get_model_path()
        
        # Validate model path
        if not self.model_config['model_exists']:
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")
        
        # Initialize model with flexible path
        self.model = YOLO(self.model_path)
        self.conf_threshold = self.model_config['confidence_threshold']
        
        # Get class names from configuration
        self.class_names = self.model_config['classes']
        
        # Get tracking classes from configuration
        self.tracking_classes = self.model_config['tracking_classes']
        
        # Initialize dispatch zones
        self.dispatch_zones = {
            1: DispatchZone([
                (582, 94),   # top-left
                (1388, 16),  # top-right
                (1426, 219), # bottom-right
                (578, 282)   # Bottom-left
            ], name="Zone 1"),
            2: DispatchZone([
                (405, 365),  # top-left
                (722,342), #op-right
                (1384, 1029),  # bottom-right
                (543, 1045)   # Bottom-left
            ], name="Zone 2"),
            3: DispatchZone([
                (1286, 369),  # top-left
                (1481, 430),  # top-right
                (1295, 1041),  # bottom-right
                (315, 1035)   # Bottom-left
            ], name="Zone 3"),
            4: DispatchZone([
                (1232, 623), # top-left
                (1736, 726), # top-right
                (1636, 1045), # bottom-right
                (934, 1044)  # Bottom-left
            ], name="Zone 4"),
            5: DispatchZone([
                (382, 409), # top-left
                (723, 395), # top-right
                (649, 1040), # bottom-right
                (132, 1036)  # Bottom-left
            ], name="Zone 5"),
            6: DispatchZone([
                (1391, 371), # top-left
                (1806, 535), # top-right
                (1604, 1044), # bottom-right
                (844, 1046)  # Bottom-left
            ], name="Zone 6")
        }
        
        # Set default active zone
        self.active_zone_id = 1
        self.dispatch_zone = self.dispatch_zones[self.active_zone_id]
        
        # Initialize box tracker
        self.box_tracker = BoxTracker()
        
        # Initialize feedback system
        self.feedback_collector = FeedbackCollector()
        self.feedback_storage = FeedbackStorage()
        
        # Initialize SFSORT tracker for box tracking
        self.sfsort_tracker = SFSORT({
            'high_th': 0.6,
            'low_th': 0.1,
            'new_track_th': 0.7,
            'frame_width': 1024,   # Adjust as needed
            'frame_height': 768,  # Adjust as needed
        })
        
        # Configure logging
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'detection_handler.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('DetectionHandler')
        self.logger.info("DetectionHandler initialized")
        
    def set_active_zone(self, zone_id):
        """Set the active dispatch zone"""
        if zone_id in self.dispatch_zones:
            self.active_zone_id = zone_id
            self.dispatch_zone = self.dispatch_zones[zone_id]
            self.logger.info(f"Active zone set to Zone {zone_id}")
            return True
        else:
            self.logger.error(f"Invalid zone ID: {zone_id}")
            return False
    
    def get_available_zones(self):
        """Get list of available zones"""
        return list(self.dispatch_zones.keys())
    
    def get_zone_info(self, zone_id):
        """Get information about a specific zone"""
        if zone_id in self.dispatch_zones:
            zone = self.dispatch_zones[zone_id]
            return {
                'id': zone_id,
                'name': zone.name,
                'is_active': zone_id == self.active_zone_id,
                'coordinates': zone.coordinates.tolist()
            }
        return None
    
    def process_video(self, video_path, gui, stop_event):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                gui.log_message("Error: Could not open video file")
                return
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            output_path = video_path.rsplit('.', 1)[0] + '_processed.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            frame_count = 0
            last_feedback_check = datetime.now()
            gui.log_message(f"Started processing video: {video_path}")
            while cap.isOpened() and not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    gui.log_message("End of video or cannot read frame.")
                    break
                self.dispatch_zone.draw_zone(frame)
                results = self.model(frame)[0]
                boxes = []
                class_ids = []
                scores = []
                for det in results.boxes:
                    box = det.xyxy[0].cpu().numpy()
                    cls_id = int(det.cls.cpu().numpy()[0])
                    score = float(det.conf.cpu().numpy()[0])
                    if cls_id in self.tracking_classes:
                        boxes.append(box)
                        class_ids.append(cls_id)
                        scores.append(score)
                # SFSORT tracking
                try:
                    tracks = self.sfsort_tracker.update(np.array(boxes), np.array(scores))
                    # Match tracks to detections by IoU
                    tracked_data = []
                    for track in tracks:
                        track_bbox = np.array(track[:4]).astype(float).flatten()
                        track_id = int(track[4]) if len(track) >= 5 else None
                        # Find best matching detection
                        best_iou = 0
                        best_idx = -1
                        for i, det_bbox in enumerate(boxes):
                            det_bbox = np.array(det_bbox).astype(float).flatten()
                            iou = compute_iou(track_bbox, det_bbox)
                            print(f"track_bbox: {track_bbox}, det_bbox: {det_bbox}, iou: {iou}, type(iou): {type(iou)}")
                            if iou > best_iou:
                                best_iou = iou
                                best_idx = i
                        if best_idx != -1:
                            tracked_data.append({
                                'track_id': track_id if track_id is not None else best_idx,
                                'bbox': track_bbox,
                                'class_id': class_ids[best_idx],
                                'confidence': scores[best_idx]
                            })
                    self.box_tracker.update_tracking(tracked_data, self.dispatch_zone, frame, gui, frame_count)
                except Exception as e:
                    self.logger.error(f"Error in SFSORT tracking: {str(e)}")
                    gui.log_message(f"Error in SFSORT tracking: {str(e)}")
                    tracked_data = [{
                        'track_id': i,
                        'bbox': box,
                        'class_id': cls_id,
                        'confidence': score
                    } for i, (box, cls_id, score) in enumerate(zip(boxes, class_ids, scores)) if cls_id in self.tracking_classes]
                    self.box_tracker.update_tracking(tracked_data, self.dispatch_zone, frame, gui, frame_count)
                self.box_tracker.draw_tracking_info_on_frame(frame)
                self.box_tracker.draw_statistics_on_frame(frame)
                current_time = datetime.now()
                if (current_time - last_feedback_check).total_seconds() >= 30:
                    self.feedback_collector.check_detection(frame, results.boxes, self.box_tracker.tracked_boxes)
                    last_feedback_check = current_time
                    gui.log_message("Checking for feedback...")
                out.write(frame)
                gui.update_video_frame(frame)
                frame_count += 1
                if frame_count % 30 == 0:
                    feedback_data = self.feedback_collector.get_feedback_data()
                    if feedback_data:
                        self.logger.info(f"Storing {len(feedback_data)} feedback entries")
                        gui.log_message(f"Storing {len(feedback_data)} feedback entries")
                        self.feedback_storage.store_feedback(feedback_data)
            feedback_data = self.feedback_collector.get_feedback_data()
            if feedback_data:
                self.logger.info(f"Storing final {len(feedback_data)} feedback entries")
                gui.log_message(f"Storing final {len(feedback_data)} feedback entries")
                self.feedback_storage.store_feedback(feedback_data)
            cap.release()
            out.release()
            self.feedback_storage.close()
            gui.reset_gui_state()
            self.logger.info("Video processing completed")
            gui.log_message("Video processing completed")
        except Exception as e:
            self.logger.error(f"Error in video processing: {str(e)}")
            gui.log_message(f"Error: {str(e)}")
            gui.reset_gui_state() 

    def _validate_box_sold(self, track_id, box_info, is_in_zone):
        """Enhanced validation for box sold detection"""
        
        pattern_matched = self._check_sale_pattern(box_info["status_history"])
        
        # Spatial validation remains the same
        spatial_valid = box_info["was_in_zone"] and not is_in_zone and \
                       box_info["frames_out_of_zone"] >= self.FRAMES_TO_CONFIRM_EXIT
        
        # Improved temporal validation
        temporal_valid = True
        if box_info["status_history"]:
            time_in_system = (datetime.now() - box_info["first_seen_time"]).total_seconds()
            last_state_change_time = (datetime.now() - box_info["last_state_change_time"]).total_seconds()
            
            # Different thresholds based on pattern
            if len(box_info["status_history"]) >= 2:
                if box_info["status_history"][-2] == self.STATUS_OPEN and \
                   box_info["status_history"][-1] == self.STATUS_CLOSE:
                    # For open->close pattern, require shorter time
                    temporal_valid = last_state_change_time >= 2.0
                else:
                    # For other patterns, use standard threshold
                    temporal_valid = time_in_system >= self.TEMPORAL_THRESHOLD
        
        # Last status validation remains the same
        last_status_valid = False
        if box_info["status_history"]:
            last_status = box_info["status_history"][-1]
            last_status_valid = last_status == self.STATUS_CLOSE
        
        if pattern_matched and spatial_valid and temporal_valid and last_status_valid:
            logger.info(f"Track {track_id} sale validated:")
            logger.info(f"- Pattern matched: {pattern_matched}")
            logger.info(f"- Spatial valid: {spatial_valid}")
            logger.info(f"- Temporal valid: {temporal_valid}")
            logger.info(f"- Last status valid: {last_status_valid}")
            return True
        return False 

    def _check_sale_pattern(self, status_history):
        """Enhanced sale pattern detection"""
        if len(status_history) < 1:
            return False

        # Pattern 1: open -> close (most common)
        if len(status_history) >= 2 and \
           status_history[-2] == self.STATUS_OPEN and \
           status_history[-1] == self.STATUS_CLOSE:
            logger.debug("Pattern 1 matched: open -> close")
            return True

        # Pattern 2: close -> open -> close (inspection pattern)
        if len(status_history) >= 3 and \
           status_history[-3] == self.STATUS_CLOSE and \
           status_history[-2] == self.STATUS_OPEN and \
           status_history[-1] == self.STATUS_CLOSE:
            logger.debug("Pattern 2 matched: close -> open -> close")
            return True

        # Pattern 3: sustained close (for pre-closed boxes)
        if len(status_history) >= 2 and \
           status_history[-1] == self.STATUS_CLOSE and \
           all(s == self.STATUS_CLOSE for s in status_history[-2:]):
            logger.debug("Pattern 3 matched: sustained close")
            return True

        return False 

    def _validate_state_change(self, track_id, new_status, box_info):
        """Enhanced state change validation"""
        if not box_info['last_status']:
            return True
        
        if box_info['last_status'] == new_status:
            return False
        
        # Prevent rapid state changes
        time_since_last_change = (datetime.now() - box_info['last_state_change_time']).total_seconds()
        if time_since_last_change < 1.0:  # Minimum 1 second between state changes
            return False
        
        # Validate state transitions
        if box_info['last_status'] == self.STATUS_CLOSE and new_status == self.STATUS_OPEN:
            # Allow reopening only if box was closed for at least 2 seconds
            return time_since_last_change >= 2.0
        
        return True 