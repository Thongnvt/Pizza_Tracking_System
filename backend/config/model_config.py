"""
Model Configuration for the Counting System
Handles flexible model paths and settings for different execution contexts.
"""

import os
import sys
from pathlib import Path

# Model Configuration
MODEL_CONFIG = {
    'default_model': 'best.pt',
    'model_type': 'yolo',  # 'yolo', 'custom', etc.
    'confidence_threshold': 0.5,
    'iou_threshold': 0.45,
    'device': 'auto',  # 'auto', 'cpu', 'cuda', 'mps'
    'classes': {
        0: 'pizza',
        1: 'box_open',
        2: 'box_close',
        3: 'box_nilon'
    },
    'tracking_classes': [1, 2],  # Classes to track (box_open, box_close)
    'model_paths': {
        'relative': 'backend/models/best.pt',
        'absolute': 'D:/Counting System/backend/models/best.pt',
        'sfsort': 'SFSORT/best.pt'
    }
}

def get_model_path():
    """
    Get the appropriate model path based on execution context.
    
    Returns:
        str: Path to the model file
    """
    # Get the current working directory
    cwd = os.getcwd()
    
    # Try different path strategies
    possible_paths = [
        # Strategy 1: Relative to current working directory
        os.path.join(cwd, MODEL_CONFIG['model_paths']['relative']),
        
        # Strategy 2: Absolute path (for GUI context)
        MODEL_CONFIG['model_paths']['absolute'],
        
        # Strategy 3: Relative to backend directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                    'models', MODEL_CONFIG['default_model']),
        
        # Strategy 4: Relative to project root
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                    'backend', 'models', MODEL_CONFIG['default_model']),
        
        # Strategy 5: SFSORT directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                    'SFSORT', MODEL_CONFIG['default_model'])
    ]
    
    # Check which path exists
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If no path exists, return the most likely one and let the caller handle the error
    return possible_paths[0]

def get_sfsort_model_path():
    """
    Get the SFSORT model path.
    
    Returns:
        str: Path to the SFSORT model file
    """
    possible_paths = [
        os.path.join(os.getcwd(), 'SFSORT', 'best.pt'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                    'SFSORT', 'best.pt'),
        'SFSORT/best.pt'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return possible_paths[0]

def validate_model_path(model_path):
    """
    Validate if the model path exists and is accessible.
    
    Args:
        model_path (str): Path to the model file
        
    Returns:
        bool: True if path is valid, False otherwise
    """
    return os.path.exists(model_path) and os.path.isfile(model_path)

def get_model_config():
    """
    Get the complete model configuration with resolved paths.
    
    Returns:
        dict: Complete model configuration
    """
    config = MODEL_CONFIG.copy()
    config['model_path'] = get_model_path()
    config['sfsort_model_path'] = get_sfsort_model_path()
    config['model_exists'] = validate_model_path(config['model_path'])
    config['sfsort_model_exists'] = validate_model_path(config['sfsort_model_path'])
    
    return config 