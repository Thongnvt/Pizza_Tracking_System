import numpy as np
from collections import defaultdict
import cv2
from datetime import datetime
import logging
import os

# Configure logging with file handler
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'box_tracker.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('BoxTracker')

class BoxTracker:
    def __init__(self):
        self.tracked_boxes = {}  
        self.box_sold_count = 0
        self.pending_boxes = set()  
        self.last_pending_count = 0  
        
        self.STATUS_OPEN = 1  # Corresponds to YOLO class_id for box_open
        self.STATUS_CLOSE = 2  # Corresponds to YOLO class_id for box_close
        
        # Enhanced parameters with recommended values
        self.HISTORY_WINDOW_SIZE = 15  # Increased from 10 to capture longer patterns
        self.FRAMES_TO_CONFIRM_EXIT = 10  # Reduced from 15 for faster response
        self.TEMPORAL_THRESHOLD = 3.0  # Reduced from 5.0 for faster transactions
        self.MIN_STATE_CHANGE_TIME = 1.0  # New parameter for state change validation
        self.SUSTAINED_CLOSE_FRAMES = 2  # New parameter for pattern 3 validation
        
        logger.info("BoxTracker initialized with parameters:")
        logger.info(f"History Window Size: {self.HISTORY_WINDOW_SIZE}")
        logger.info(f"Frames to Confirm Exit: {self.FRAMES_TO_CONFIRM_EXIT}")
        logger.info(f"Temporal Threshold: {self.TEMPORAL_THRESHOLD}")
        logger.info(f"Min State Change Time: {self.MIN_STATE_CHANGE_TIME}")
        logger.info(f"Sustained Close Frames: {self.SUSTAINED_CLOSE_FRAMES}")
        
    def update_tracking(self, tracked_data, dispatch_zone, frame, gui, frame_count):
        logger.info(f"Processing frame {frame_count} with {len(tracked_data)} tracked items")
        gui.log_message(f"Frame {frame_count}: {len(tracked_data)} tracked items")
        current_frame_tracked_ids = set()
        
        tracked_items = []
        for item in tracked_data:
            try:
                if hasattr(item, 'xyxy'):  
                    bbox = item.xyxy[0].cpu().numpy()
                    cls = int(item.cls.cpu().numpy()[0])
                    conf = float(item.conf.cpu().numpy()[0])
                    track_id = getattr(item, 'track_id', f"{int(bbox[0])}_{int(bbox[1])}")
                else:  
                    bbox = item['bbox']
                    cls = item['class_id']
                    conf = item['confidence']
                    track_id = item['track_id']
                
                tracked_items.append({
                    'bbox': bbox,
                    'class_id': cls,
                    'confidence': conf,
                    'track_id': track_id
                })
                logger.debug(f"Processed track {track_id}: class={cls}, conf={conf:.2f}")
            except Exception as e:
                logger.warning(f"Error processing tracked item: {str(e)}")
                gui.log_message(f"Error processing tracked item: {str(e)}")
                continue
        
        previous_pending = self.pending_boxes.copy()
        self.pending_boxes.clear()
        
        for item in tracked_items:
            bbox = item['bbox']
            class_id = item['class_id']
            track_id = item['track_id']
            
            current_frame_tracked_ids.add(track_id)
            
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            is_in_zone = dispatch_zone.is_point_in_zone((center_x, center_y))
            
            if track_id not in self.tracked_boxes:
                logger.info(f"New track detected: {track_id}")
                gui.log_message(f"New track detected: {track_id}")
                self.tracked_boxes[track_id] = {
                    'status_history': [],
                    'last_seen_frame': 0,
                    'in_dispatch_zone': is_in_zone,
                    'frames_out_of_zone': 0,
                    'potential_sale_pattern_matched': False,
                    'was_in_zone': is_in_zone,
                    'last_status': None,
                    'last_bbox': bbox,
                    'first_seen_frame': frame_count,
                    'first_seen_time': datetime.now(),
                    'last_state_change_time': datetime.now()
                }
            
            box_info = self.tracked_boxes[track_id]
            box_info['last_bbox'] = bbox
            
            current_status = self._map_class_to_status(class_id)
            self._update_box_info(track_id, box_info, current_status, is_in_zone)
            
            box_info['last_seen_frame'] = frame_count
            
            if is_in_zone and current_status == self.STATUS_OPEN:
                self.pending_boxes.add(track_id)
                logger.info(f"Track {track_id} added to pending boxes")
                gui.log_message(f"Track {track_id} added to pending boxes")
            
            if self._validate_box_sold(track_id, box_info, is_in_zone):
                self.box_sold_count += 1
                logger.info(f"Track {track_id}: BOX SOLD! Total sold: {self.box_sold_count}")
                gui.log_message(f"Track {track_id}: BOX SOLD! Total sold: {self.box_sold_count}")
                gui.log_message(f"BOX SOLD! Track ID: {track_id}")
                del self.tracked_boxes[track_id]
                continue
        
        self._cleanup_old_tracks(current_frame_tracked_ids, frame_count)
        
        current_pending_count = len(self.pending_boxes)
        if current_pending_count != self.last_pending_count:
            self.last_pending_count = current_pending_count
            logger.info(f"Pending boxes count updated: {current_pending_count}")
            gui.log_message(f"Pending boxes count updated: {current_pending_count}")
        gui.update_counts(current_pending_count, self.box_sold_count)

    def _validate_state_change(self, track_id, new_status, box_info):
        """Enhanced state change validation"""
        if not box_info['last_status']:
            return True
            
        if box_info['last_status'] == new_status:
            return False
            
        # Prevent rapid state changes
        time_since_last_change = (datetime.now() - box_info['last_state_change_time']).total_seconds()
        if time_since_last_change < self.MIN_STATE_CHANGE_TIME:
            return False
            
        # Validate state transitions
        if box_info['last_status'] == self.STATUS_CLOSE and new_status == self.STATUS_OPEN:
            # Allow reopening only if box was closed for at least 2 seconds
            return time_since_last_change >= 2.0
            
        return True

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

    def _cleanup_old_tracks(self, current_frame_tracked_ids, frame_count):
        """Clean up tracks that haven't been seen for a while"""
        boxes_to_remove = []
        for track_id, box_info in list(self.tracked_boxes.items()):
            if track_id not in current_frame_tracked_ids:
                box_info["last_seen_frame"] += 1
                if box_info["last_seen_frame"] > self.FRAMES_TO_CONFIRM_EXIT * 2:
                    boxes_to_remove.append(track_id)
            else:
                box_info["last_seen_frame"] = 0

        for track_id in boxes_to_remove:
            logger.info(f"Track {track_id}: Removed due to inactivity.")
            del self.tracked_boxes[track_id]

    def _map_class_to_status(self, class_id):
        if class_id == 1:  # box_open
            return self.STATUS_OPEN
        elif class_id == 2:  # box_close
            return self.STATUS_CLOSE
        return None

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
           all(s == self.STATUS_CLOSE for s in status_history[-self.SUSTAINED_CLOSE_FRAMES:]):
            logger.debug("Pattern 3 matched: sustained close")
            return True

        return False

    def draw_tracking_info_on_frame(self, frame):
        for track_id, box_info in self.tracked_boxes.items():
            if 'last_bbox' not in box_info:
                continue
                
            bbox = box_info['last_bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            status_text = "Unknown"
            if box_info["status_history"]:
                last_status = box_info["status_history"][-1]
                if last_status == self.STATUS_OPEN: 
                    status_text = "Open"
                    color = (0, 255, 0)  # Green for open
                elif last_status == self.STATUS_CLOSE: 
                    status_text = "Close"
                    color = (0, 0, 255)  # Red for closed

            label = f"ID: {track_id} - {status_text}"
            if box_info["potential_sale_pattern_matched"]:
                label += " (Pattern Matched)"
                color = (255, 255, 0)  # Yellow for pattern matched

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def draw_statistics_on_frame(self, frame):
        stats_text = [
            f"Boxes Sold: {self.box_sold_count}",
            f"Pending Boxes: {len(self.pending_boxes)}"
        ]
        
        
        current_open_boxes = sum(1 for box_info in self.tracked_boxes.values() 
                                 if box_info["in_dispatch_zone"] and 
                                    box_info["status_history"] and 
                                    box_info["status_history"][-1] == self.STATUS_OPEN)
        current_close_boxes = sum(1 for box_info in self.tracked_boxes.values() 
                                  if box_info["in_dispatch_zone"] and 
                                     box_info["status_history"] and 
                                     box_info["status_history"][-1] == self.STATUS_CLOSE)

        stats_text.append(f"Open in Zone: {current_open_boxes}")
        stats_text.append(f"Closed in Zone: {current_close_boxes}")

        for i, text in enumerate(stats_text):
            cv2.putText(frame, text, (10, 30 + i*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def _update_box_info(self, track_id, box_info, current_status, is_in_zone):
        """Enhanced box info update with additional validation"""
        # Update status history
        if current_status is not None:
            if self._validate_state_change(track_id, current_status, box_info):
                box_info['status_history'].append(current_status)
                if len(box_info['status_history']) > self.HISTORY_WINDOW_SIZE:
                    box_info['status_history'].pop(0)
                box_info['last_status'] = current_status
                box_info['last_state_change_time'] = datetime.now()
            
        # Update zone information
        if is_in_zone:
            box_info['was_in_zone'] = True
            box_info['frames_out_of_zone'] = 0
        else:
            box_info['frames_out_of_zone'] += 1
        
        # Update tracking confidence
        if 'tracking_confidence' not in box_info:
            box_info['tracking_confidence'] = 1.0
        else:
            # Decrease confidence when box is lost or state changes rapidly
            if not is_in_zone:
                box_info['tracking_confidence'] *= 0.95
            if current_status != box_info.get('last_status'):
                box_info['tracking_confidence'] *= 0.9
