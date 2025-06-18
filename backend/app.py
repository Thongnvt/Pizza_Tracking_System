from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import sys
import os
import logging
import time
from datetime import datetime
import json
import cv2
import numpy as np
import base64
import threading
import queue
from werkzeug.utils import secure_filename
from utils.detection_handler import DetectionHandler
from utils.module_status import ModuleStatus
from pathlib import Path
from collections import defaultdict
import tempfile
import shutil
from utils.import_helper import get_model_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the root directory to Python path
root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

from SFSORT.SFSORT import SFSORT
import numpy as np
import cv2

class VideoProcessor:
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.streams = {}
        self.frame_queues = {}
        self.processing_threads = {}
        self.stop_events = {}
        
        # Initialize detection handler with full workflow
        self.detection_handler = DetectionHandler()
        
        # Statistics tracking
        self.statistics = {
            'total_detections': 0,
            'current_session': 0,
            'boxes_sold': 0,
            'pending_boxes': 0,
            'open_boxes_in_zone': 0,
            'closed_boxes_in_zone': 0
        }
        
        # Mock GUI handler for socket communication
        self.gui_handler = SocketGUIHandler(socketio_instance)
        
        logger.info("VideoProcessor initialized with full tracking system")

    def start_stream(self, source_id, source_type='camera'):
        """Start video stream processing with full tracking workflow"""
        try:
            if source_id in self.streams:
                logger.warning(f"Stream {source_id} is already running")
                return False
            
            # Create stop event for this stream
            self.stop_events[source_id] = threading.Event()
            
            # Create frame queue
            self.frame_queues[source_id] = queue.Queue(maxsize=10)
            
            # Start processing thread
            self.processing_threads[source_id] = threading.Thread(
                target=self._process_stream,
                args=(source_id, source_type)
            )
            self.processing_threads[source_id].daemon = True
            self.processing_threads[source_id].start()
            
            logger.info(f"Started stream {source_id} with type {source_type}")
            self.socketio.emit('processing_status', {
                'source': source_id,
                'status': 'started',
                'message': f'Started processing {source_type} stream'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting stream {source_id}: {str(e)}")
            return False

    def stop_stream(self, source_id):
        """Stop video stream processing"""
        try:
            if source_id in self.stop_events:
                self.stop_events[source_id].set()
                
            if source_id in self.processing_threads:
                self.processing_threads[source_id].join(timeout=2)
                
            # Clean up
            if source_id in self.streams:
                self.streams[source_id].release()
                del self.streams[source_id]
                
            if source_id in self.frame_queues:
                del self.frame_queues[source_id]
                
            if source_id in self.processing_threads:
                del self.processing_threads[source_id]
                
            if source_id in self.stop_events:
                del self.stop_events[source_id]
                
            logger.info(f"Stopped stream {source_id}")
            self.socketio.emit('processing_status', {
                'source': source_id,
                'status': 'stopped',
                'message': 'Processing stopped'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping stream {source_id}: {str(e)}")
            return False

    def _process_stream(self, source_id, source_type):
        """Process video stream with full tracking workflow"""
        try:
            if source_type == 'camera':
                cap = cv2.VideoCapture(0)  # Use default camera
            else:
                # For uploaded videos, source_id should be the file path
                cap = cv2.VideoCapture(source_id)
                
            if not cap.isOpened():
                logger.error(f"Could not open video source: {source_id}")
                self.socketio.emit('processing_error', {
                    'source': source_id,
                    'message': 'Could not open video source'
                })
                return
                
            self.streams[source_id] = cap
            
            frame_count = 0
            last_stats_update = time.time()
            
            logger.info(f"Started processing {source_type} stream: {source_id}")
            self.socketio.emit('processing_status', {
                'source': source_id,
                'status': 'processing',
                'message': 'Processing video stream'
            })
            
            while cap.isOpened() and not self.stop_events[source_id].is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.info(f"End of video stream: {source_id}")
                    break
                    
                # Process frame with full tracking workflow
                processed_frame = self._process_frame_with_tracking(frame, source_id, frame_count)
                
                # Send frame to frontend
                if processed_frame is not None:
                    # Convert frame to base64 for transmission
                    _, buffer = cv2.imencode('.jpg', processed_frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    self.socketio.emit('video_frame', {
                        'source': source_id,
                        'frame': frame_base64,
                        'frame_count': frame_count
                    }, room=f'video_{source_id}')
                
                frame_count += 1
                
                # Update statistics periodically
                if time.time() - last_stats_update > 1.0:  # Every second
                    self._update_statistics()
                    last_stats_update = time.time()
                    
            # Cleanup
            cap.release()
            logger.info(f"Finished processing stream: {source_id}")
            self.socketio.emit('processing_status', {
                'source': source_id,
                'status': 'completed',
                'message': 'Video processing completed'
            })
            
        except Exception as e:
            logger.error(f"Error in stream processing: {str(e)}")
            self.socketio.emit('processing_error', {
                'source': source_id,
                'message': f'Processing error: {str(e)}'
            })

    def _process_frame_with_tracking(self, frame, source_id, frame_count):
        """Process frame with full tracking, counting, and feedback system"""
        try:
            # Get detections from YOLO model
            results = self.detection_handler.model(frame)[0]
            
            # Extract detection data for SFSORT tracking
            boxes = []
            class_ids = []
            scores = []
            
            for det in results.boxes:
                box = det.xyxy[0].cpu().numpy()
                cls_id = int(det.cls.cpu().numpy()[0])
                score = float(det.conf.cpu().numpy()[0])
                
                # Only track relevant classes (box_open, box_close)
                if cls_id in self.detection_handler.tracking_classes:
                    boxes.append(box)
                    class_ids.append(cls_id)
                    scores.append(score)
            
            # Use SFSORT tracking (same as local GUI)
            tracked_data = []
            if boxes:
                try:
                    tracks = self.detection_handler.sfsort_tracker.update(np.array(boxes), np.array(scores))
                    # Match tracks to detections by IoU
                    for track in tracks:
                        track_bbox = np.array(track[:4]).astype(float).flatten()
                        track_id = int(track[4]) if len(track) >= 5 else None
                        # Find best matching detection
                        best_iou = 0
                        best_idx = -1
                        for i, det_bbox in enumerate(boxes):
                            det_bbox = np.array(det_bbox).astype(float).flatten()
                            iou = self._compute_iou(track_bbox, det_bbox)
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
                except Exception as e:
                    logger.error(f"Error in SFSORT tracking: {str(e)}")
                    # Fallback to simple tracking if SFSORT fails
                    tracked_data = [{
                        'track_id': i,
                        'bbox': box,
                        'class_id': cls_id,
                        'confidence': score
                    } for i, (box, cls_id, score) in enumerate(zip(boxes, class_ids, scores))]
            
            # Update tracking with full workflow
            if tracked_data:
                self.detection_handler.box_tracker.update_tracking(
                    tracked_data, 
                    self.detection_handler.dispatch_zone, 
                    frame, 
                    self.gui_handler, 
                    frame_count
                )
            
            # Draw tracking information on frame
            self.detection_handler.box_tracker.draw_tracking_info_on_frame(frame)
            self.detection_handler.box_tracker.draw_statistics_on_frame(frame)
            
            # Draw dispatch zone
            self.detection_handler.dispatch_zone.draw_zone(frame)
            
            # Check for feedback periodically (every 30 frames)
            if frame_count % 30 == 0:
                self.detection_handler.feedback_collector.check_detection(
                    frame, 
                    results.boxes, 
                    self.detection_handler.box_tracker.tracked_boxes
                )
                
                # Store feedback data
                feedback_data = self.detection_handler.feedback_collector.get_feedback_data()
                if feedback_data:
                    logger.info(f"Storing {len(feedback_data)} feedback entries")
                    self.detection_handler.feedback_storage.store_feedback(feedback_data)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error in frame processing: {str(e)}")
            return frame

    def _compute_iou(self, boxA, boxB):
        """Compute IoU between two bounding boxes"""
        import numpy as np
        
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

    def _update_statistics(self):
        """Update and emit statistics"""
        try:
            # Get current statistics from box tracker
            self.statistics['boxes_sold'] = self.detection_handler.box_tracker.box_sold_count
            self.statistics['pending_boxes'] = len(self.detection_handler.box_tracker.pending_boxes)
            
            # Count boxes in zone
            current_open_boxes = sum(1 for box_info in self.detection_handler.box_tracker.tracked_boxes.values() 
                                   if box_info.get("in_dispatch_zone") and 
                                      box_info.get("status_history") and 
                                      box_info["status_history"][-1] == self.detection_handler.box_tracker.STATUS_OPEN)
            
            current_close_boxes = sum(1 for box_info in self.detection_handler.box_tracker.tracked_boxes.values() 
                                    if box_info.get("in_dispatch_zone") and 
                                       box_info.get("status_history") and 
                                       box_info["status_history"][-1] == self.detection_handler.box_tracker.STATUS_CLOSE)
            
            self.statistics['open_boxes_in_zone'] = current_open_boxes
            self.statistics['closed_boxes_in_zone'] = current_close_boxes
            
            # Emit statistics to frontend
            self.socketio.emit('statistics_update', self.statistics)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {str(e)}")

    def get_frame(self, source_id):
        """Get processed frame from queue"""
        if source_id in self.frame_queues and not self.frame_queues[source_id].empty():
            return self.frame_queues[source_id].get()
        return None

    def set_active_zone(self, zone_id):
        """Set the active dispatch zone"""
        try:
            success = self.detection_handler.set_active_zone(zone_id)
            if success:
                logger.info(f"Active zone set to Zone {zone_id}")
                self.socketio.emit('zone_updated', {
                    'zone_id': zone_id,
                    'status': 'active'
                })
            return success
        except Exception as e:
            logger.error(f"Error setting active zone: {str(e)}")
            return False

    def get_available_zones(self):
        """Get list of available zones"""
        return self.detection_handler.get_available_zones()

    def get_zone_info(self, zone_id):
        """Get information about a specific zone"""
        return self.detection_handler.get_zone_info(zone_id)

    def get_statistics(self):
        """Get current statistics"""
        return self.statistics


class SocketGUIHandler:
    """Mock GUI handler that uses Socket.IO for communication"""
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        
    def log_message(self, message):
        """Send log message to frontend"""
        self.socketio.emit('log_message', {
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def update_video_frame(self, frame):
        """Update video frame (handled by VideoProcessor)"""
        pass
        
    def update_counts(self, pending_count, sold_count):
        """Update counts and emit to frontend"""
        self.socketio.emit('counts_update', {
            'pending_boxes': pending_count,
            'boxes_sold': sold_count,
            'timestamp': datetime.now().isoformat()
        })
        
    def reset_gui_state(self):
        """Reset GUI state"""
        self.socketio.emit('gui_reset', {
            'message': 'Processing completed',
            'timestamp': datetime.now().isoformat()
        })

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Configure maximum file size (2GB)
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=2 * 1024 * 1024 * 1024)
    
    # Initialize video processor with socketio instance
    video_processor = VideoProcessor(socketio)
    
    # Initialize detection handler
    detection_handler = DetectionHandler()
    
    # Initialize module status
    module_status = {
        "tracker": ModuleStatus(),
        "camera": ModuleStatus(),
        "detection": ModuleStatus(),
        "api": ModuleStatus()
    }

    # Configure upload folder
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')

    @socketio.on('join_video')
    def handle_join_video(data):
        source_id = data.get('source')
        if source_id:
            room = f'video_{source_id}'
            join_room(room)
            logger.info(f'Client joined room: {room}')

    @socketio.on('leave_video')
    def handle_leave_video(data):
        source_id = data.get('source')
        if source_id:
            room = f'video_{source_id}'
            leave_room(room)
            logger.info(f'Client left room: {room}')

    @app.route('/api/video-sources', methods=['GET'])
    def get_video_sources():
        """Get available video sources"""
        try:
            # Return fixed sources: webcam and upload option
            return jsonify({
                "status": "success",
                "sources": ["1", "2"]  # 1 for webcam, 2 for upload
            })
        except Exception as e:
            logger.error(f"Error getting video sources: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/zones', methods=['GET'])
    def get_zones():
        """Get available detection zones"""
        try:
            # Get zones from video processor
            available_zones = video_processor.get_available_zones()
            return jsonify({
                "status": "success",
                "zones": [str(zone) for zone in available_zones]
            })
        except Exception as e:
            logger.error(f"Error getting zones: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/zone-info', methods=['GET'])
    def get_zone_info():
        """Get detailed information about zones"""
        try:
            zone_info = []
            for zone_id in video_processor.get_available_zones():
                zone = video_processor.get_zone_info(zone_id)
                if zone:
                    zone_info.append({
                        "zoneId": str(zone_id),
                        "status": "active" if zone_id == video_processor.detection_handler.active_zone_id else "inactive",
                        "lastDetection": datetime.now().isoformat(),
                        "count": 0,  # You might want to track actual counts
                        "name": zone['name'],
                        "coordinates": zone['coordinates']
                    })
            return jsonify(zone_info)
        except Exception as e:
            logger.error(f"Error getting zone info: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """Get detection statistics"""
        try:
            # Get real statistics from video processor
            stats = video_processor.get_statistics()
            return jsonify({
                "status": "success",
                "total": stats['total_detections'],
                "current": stats['current_session'],
                "boxes_sold": stats['boxes_sold'],
                "pending_boxes": stats['pending_boxes'],
                "open_boxes_in_zone": stats['open_boxes_in_zone'],
                "closed_boxes_in_zone": stats['closed_boxes_in_zone'],
                "lastHour": 0,  # Could be implemented with time-based tracking
                "last24Hours": 0  # Could be implemented with time-based tracking
            })
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint that returns API information and module status"""
        logger.debug("Root endpoint accessed")
        try:
            module_status["api"].update(success=True)
            return jsonify({
                "status": "running",
                "message": "SFSORT Backend Server",
                "modules": {name: status.to_dict() for name, status in module_status.items()},
                "endpoints": {
                    "health": "/api/health",
                    "initialize": "/api/initialize",
                    "update": "/api/update",
                    "status": "/api/status",
                    "video_sources": "/api/video-sources",
                    "zones": "/api/zones",
                    "statistics": "/api/statistics",
                    "zone_info": "/api/zone-info"
                }
            })
        except Exception as e:
            logger.error(f"Error in root endpoint: {str(e)}")
            module_status["api"].update(success=False, error=e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get detailed status of all modules"""
        try:
            return jsonify({
                "status": "success",
                "modules": {name: status.to_dict() for name, status in module_status.items()},
                "server_uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0
            })
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        logger.debug("Health check endpoint accessed")
        try:
            module_status["api"].update(success=True)
            return jsonify({
                "status": "healthy", 
                "message": "Backend is running",
                "modules": {name: status.to_dict() for name, status in module_status.items()}
            })
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            module_status["api"].update(success=False, error=e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/initialize', methods=['POST'])
    def initialize_tracker():
        """Initialize the detection handler"""
        logger.debug("Initialize endpoint accessed")
        try:
            config = request.json
            logger.debug(f"Received config: {config}")
            # Initialize detection handler with config if needed
            module_status["tracker"].update(success=True)
            return jsonify({"status": "success", "message": "Detection handler initialized"})
        except Exception as e:
            logger.error(f"Error initializing detection handler: {str(e)}")
            module_status["tracker"].update(success=False, error=e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/update', methods=['POST'])
    def update_tracker():
        """Update the detection handler with new detections"""
        logger.debug("Update endpoint accessed")
        try:
            data = request.json
            logger.debug(f"Received data: {data}")
            # Process detections using detection handler
            module_status["tracker"].update(success=True)
            return jsonify({
                "status": "success",
                "message": "Detection handler updated"
            })
        except Exception as e:
            logger.error(f"Error updating detection handler: {str(e)}")
            module_status["tracker"].update(success=False, error=e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/upload-video', methods=['POST'])
    def upload_video():
        try:
            if 'video' not in request.files:
                return jsonify({'error': 'No video file provided'}), 400

            file = request.files['video']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Supported formats: mp4, avi, mov, mkv, wmv, flv, webm'}), 400

            # Check file size (additional validation)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            if file_size > max_size:
                return jsonify({'error': f'File size ({file_size / (1024*1024*1024):.1f}GB) exceeds maximum allowed size (2GB)'}), 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file in chunks for large files
            chunk_size = 8192  # 8KB chunks
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)

            logger.info(f"Video uploaded successfully: {filename} ({file_size / (1024*1024):.1f}MB)")
            
            # Emit upload success event
            socketio.emit('upload_success', {
                'filename': filename,
                'filepath': filepath,
                'size': file_size
            })

            return jsonify({
                'status': 'success',
                'message': 'Video uploaded successfully',
                'videoPath': filepath,
                'filename': filename,
                'size': file_size
            })

        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500

    @app.route('/api/process-toggle', methods=['POST'])
    def process_toggle():
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            source = data.get('source')
            action = data.get('action')

            if not source or not action:
                return jsonify({'error': 'Missing source or action'}), 400

            logger.info(f"Processing toggle request - Source: {source}, Action: {action}")

            # Ensure uploads directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            if action == 'start':
                # Handle webcam (source 1) or uploaded video
                if source == '0':  # Webcam
                    source_type = 'camera'
                else:  # Uploaded video
                    if not os.path.exists(source):
                        return jsonify({'error': f'Video file not found: {source}'}), 400
                    source_type = 'file'

                try:
                    video_processor.start_stream(source, source_type)
                    logger.info(f"Started processing for source: {source} (type: {source_type})")
                    
                    # Emit processing started event
                    socketio.emit('processing_started', {
                        'source': source,
                        'type': source_type
                    })
                    
                    return jsonify({
                        'status': 'success', 
                        'message': f'Processing started for source: {source}',
                        'action': 'started'
                    })
                except Exception as e:
                    logger.error(f"Error starting processing: {str(e)}")
                    socketio.emit('processing_error', {
                        'source': source,
                        'error': str(e)
                    })
                    return jsonify({'error': f'Failed to start processing: {str(e)}'}), 500
                    
            elif action == 'stop':
                try:
                    video_processor.stop_stream(source)
                    logger.info(f"Stopped processing for source: {source}")
                    
                    # Emit processing completed event
                    socketio.emit('processing_completed', {
                        'source': source,
                        'message': 'Video processing completed successfully'
                    })
                    
                    return jsonify({
                        'status': 'success', 
                        'message': f'Processing stopped for source: {source}',
                        'action': 'stopped'
                    })
                except Exception as e:
                    logger.error(f"Error stopping processing: {str(e)}")
                    return jsonify({'error': f'Failed to stop processing: {str(e)}'}), 500
            else:
                return jsonify({'error': 'Invalid action. Must be "start" or "stop"'}), 400

        except Exception as e:
            logger.error(f"Error in process_toggle: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/set-zone', methods=['POST'])
    def set_active_zone():
        """Set the active detection zone"""
        try:
            data = request.json
            if not data or 'zone_id' not in data:
                return jsonify({'error': 'Zone ID is required'}), 400

            zone_id = int(data['zone_id'])
            success = video_processor.set_active_zone(zone_id)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Active zone set to Zone {zone_id}'
                })
            else:
                return jsonify({'error': f'Failed to set zone {zone_id}'}), 400
                
        except Exception as e:
            logger.error(f"Error setting active zone: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        logger.error(f"404 error: {request.url}")
        module_status["api"].update(success=False, error=f"Resource not found: {request.url}")
        return jsonify({
            "status": "error",
            "message": f"Resource not found: {request.url}",
            "available_endpoints": ["/", "/api/health", "/api/initialize", "/api/update", "/api/status"]
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"500 error: {str(error)}")
        module_status["api"].update(success=False, error=str(error))
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(error)
        }), 500

    return app, socketio

def main():
    """Main function to run the Flask application"""
    logger.info("Starting Flask server...")
    try:
        app, socketio = create_app()
        app.start_time = time.time()  # Record server start time
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 