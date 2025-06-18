from pymongo import MongoClient
from datetime import datetime
import json
import numpy as np
from bson import ObjectId
import cv2
import base64
import logging
from .import_helper import get_mongodb_uri, get_mongodb_config_dict
import numbers
import os
import sqlite3
from pathlib import Path
import threading

class FeedbackStorage:
    def __init__(self):
        self.db_path = 'backend/db/feedback.db'
        self.json_path = 'backend/db/feedback_data.json'
        self._local = threading.local()
        self.initialize_storage()
        
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('FeedbackStorage')
        
       
        self.uri = get_mongodb_uri()
        self.client = None
        self.db = None
        self.feedback_collection = None
        self.model_metrics_collection = None
        
        # Get MongoDB config
        self.mongodb_config = get_mongodb_config_dict()
        
       
        self._connect()
        
    def initialize_storage(self):
        """Initialize both SQLite and JSON storage"""
       
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
       
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump([], f)
        
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    track_id TEXT,
                    class_id INTEGER,
                    confidence REAL,
                    is_correct BOOLEAN,
                    bbox TEXT,
                    issues TEXT,
                    tracking_info TEXT
                )
            ''')
            conn.commit()
    
    def _get_connection(self):
        """Get a thread-local SQLite connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
        return self._local.conn
        
    def _connect(self):
        """Connect to MongoDB and initialize collections"""
        try:
            self.client = MongoClient(self.uri)
           
            self.client.admin.command('ping')
            self.logger.info("Successfully connected to MongoDB")
            
            
            self.db = self.client[self.mongodb_config['database']]
            self.feedback_collection = self.db[self.mongodb_config['collections']['feedback']]
            self.model_metrics_collection = self.db[self.mongodb_config['collections']['metrics']]
            
            
            self.feedback_collection.create_index([('timestamp', 1)])
            self.feedback_collection.create_index([('processed', 1)])
            self.model_metrics_collection.create_index([('timestamp', 1)])
            
            self.logger.info("Database and collections initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        
    def store_feedback(self, feedback_data):
        """Store feedback data in both SQLite and JSON formats"""
        try:
           
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for feedback in feedback_data:
                    cursor.execute('''
                        INSERT INTO feedback (
                            timestamp, track_id, class_id, confidence,
                            is_correct, bbox, issues, tracking_info
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        feedback['timestamp'].isoformat(),
                        feedback['detection'].get('track_id'),
                        feedback['detection'].get('class'),
                        feedback['detection'].get('confidence'),
                        feedback['is_correct'],
                        json.dumps(feedback['detection'].get('bbox')),
                        json.dumps(feedback.get('issues', [])),
                        json.dumps(feedback.get('tracking_info', {}))
                    ))
                conn.commit()
            
            # Store in JSON
            with open(self.json_path, 'r+') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
                
                existing_data.extend(feedback_data)
                
                
                f.seek(0)
                json.dump(existing_data, f, indent=2, default=str)
                f.truncate()
            
         
            if self.feedback_collection is not None:

                mongo_feedback = []
                for feedback in feedback_data:
                    mongo_feedback.append({
                        'timestamp': feedback['timestamp'],
                        'detection': {
                            'bbox': feedback['detection']['bbox'],
                            'class': feedback['detection']['class'],
                            'confidence': float(feedback['detection']['confidence']),
                            'track_id': feedback['detection'].get('track_id')
                        },
                        'is_correct': feedback['is_correct'],
                        'issues': feedback.get('issues', []),
                        'tracking_info': feedback.get('tracking_info'),
                        'user_feedback': feedback.get('user_feedback', True),
                        'processed': False
                    })
                
                
                if mongo_feedback:
                    self.feedback_collection.insert_many(mongo_feedback)
                    self.logger.info(f"Stored {len(mongo_feedback)} feedback entries in MongoDB")
            
            self.logger.info(f"Stored {len(feedback_data)} feedback entries")
            
        except Exception as e:
            self.logger.error(f"Error storing feedback: {str(e)}")
            raise
    
    def get_feedback_stats(self):
        """Get statistics about stored feedback"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                        AVG(confidence) as avg_confidence,
                        COUNT(DISTINCT track_id) as unique_tracks
                    FROM feedback
                ''')
                
                stats = cursor.fetchone()
                return {
                    'total_feedback': stats[0],
                    'correct_detections': stats[1],
                    'average_confidence': stats[2],
                    'unique_tracks': stats[3]
                }
            
        except Exception as e:
            self.logger.error(f"Error getting feedback stats: {str(e)}")
            return None
    
    def get_track_feedback(self, track_id):
        """Get all feedback for a specific track"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM feedback
                    WHERE track_id = ?
                    ORDER BY timestamp DESC
                ''', (track_id,))
                
                columns = [description[0] for description in cursor.description]
                feedback = []
                
                for row in cursor.fetchall():
                    feedback.append(dict(zip(columns, row)))
                
                return feedback
            
        except Exception as e:
            self.logger.error(f"Error getting track feedback: {str(e)}")
            return None
    
    def get_recent_feedback(self, limit=100):
        """Get most recent feedback entries"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM feedback
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                columns = [description[0] for description in cursor.description]
                feedback = []
                
                for row in cursor.fetchall():
                    feedback.append(dict(zip(columns, row)))
                
                return feedback
            
        except Exception as e:
            self.logger.error(f"Error getting recent feedback: {str(e)}")
            return None
    
    def export_feedback(self, format='json', path=None):
        """Export feedback data to a file"""
        try:
            if format == 'json':
                if path is None:
                    path = f'feedback_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                
                with open(path, 'w') as f:
                    json.dump(self.get_recent_feedback(), f, indent=2, default=str)
                    
            elif format == 'csv':
                if path is None:
                    path = f'feedback_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                
                import csv
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(['timestamp', 'track_id', 'class_id', 'confidence',
                                   'is_correct', 'bbox', 'issues', 'tracking_info'])
                    
                    # Write data
                    for feedback in self.get_recent_feedback():
                        writer.writerow([
                            feedback['timestamp'],
                            feedback['track_id'],
                            feedback['class_id'],
                            feedback['confidence'],
                            feedback['is_correct'],
                            feedback['bbox'],
                            feedback['issues'],
                            feedback['tracking_info']
                        ])
            
            self.logger.info(f"Exported feedback to {path}")
            return path
            
        except Exception as e:
            self.logger.error(f"Error exporting feedback: {str(e)}")
            return None
    
    def close(self):
        """Close database connections"""
        try:
            if hasattr(self._local, 'conn'):
                self._local.conn.close()
                del self._local.conn
            if self.client:
                self.client.close()
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {str(e)}")

def to_python_type(val):
    if isinstance(val, np.generic):
        return val.item()
    if isinstance(val, (list, tuple)):
        return [to_python_type(x) for x in val]
    if isinstance(val, dict):
        return {k: to_python_type(v) for k, v in val.items()}
    return val 