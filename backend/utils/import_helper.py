"""
Import helper module to handle different import scenarios
for both GUI (tkinter) and local frontend execution contexts.
"""

import sys
import os
from importlib import import_module

def get_mongodb_config():
    """
    Dynamically import MongoDB configuration based on execution context.
    
    Returns:
        tuple: (get_mongodb_uri function, MONGODB_CONFIG dict)
    """
    try:
        # First try the relative import (for GUI/tkinter context)
        try:
            from ..config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
            return get_mongodb_uri, MONGODB_CONFIG
        except (ImportError, ValueError):
            pass
        
        # Then try the absolute import (for local frontend context)
        try:
            from config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
            return get_mongodb_uri, MONGODB_CONFIG
        except ImportError:
            pass
        
        # If both fail, try to determine the correct path dynamically
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        
        # Add backend directory to path if not already there
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        try:
            from config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
            return get_mongodb_uri, MONGODB_CONFIG
        except ImportError:
            pass
        
        # Last resort: try to import using the full path
        config_path = os.path.join(backend_dir, 'config', 'mongodb_config.py')
        if os.path.exists(config_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("mongodb_config", config_path)
            mongodb_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mongodb_config_module)
            return mongodb_config_module.get_mongodb_uri, mongodb_config_module.MONGODB_CONFIG
        
        raise ImportError("Could not import MongoDB configuration from any expected location")
        
    except Exception as e:
        raise ImportError(f"Failed to import MongoDB configuration: {str(e)}")

def get_model_config():
    """
    Dynamically import model configuration based on execution context.
    
    Returns:
        tuple: (get_model_path function, get_model_config function, MODEL_CONFIG dict)
    """
    try:
        # First try the relative import (for GUI/tkinter context)
        try:
            from ..config.model_config import get_model_path, get_model_config as get_full_config, MODEL_CONFIG
            return get_model_path, get_full_config, MODEL_CONFIG
        except (ImportError, ValueError):
            pass
        
        # Then try the absolute import (for local frontend context)
        try:
            from config.model_config import get_model_path, get_model_config as get_full_config, MODEL_CONFIG
            return get_model_path, get_full_config, MODEL_CONFIG
        except ImportError:
            pass
        
        # If both fail, try to determine the correct path dynamically
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        
        # Add backend directory to path if not already there
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        try:
            from config.model_config import get_model_path, get_model_config as get_full_config, MODEL_CONFIG
            return get_model_path, get_full_config, MODEL_CONFIG
        except ImportError:
            pass
        
        # Last resort: try to import using the full path
        config_path = os.path.join(backend_dir, 'config', 'model_config.py')
        if os.path.exists(config_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("model_config", config_path)
            model_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(model_config_module)
            return model_config_module.get_model_path, model_config_module.get_model_config, model_config_module.MODEL_CONFIG
        
        raise ImportError("Could not import model configuration from any expected location")
        
    except Exception as e:
        raise ImportError(f"Failed to import model configuration: {str(e)}")

# Convenience functions for direct access
def get_mongodb_uri():
    """Get MongoDB URI using the dynamic import helper"""
    return get_mongodb_config()[0]()

def get_mongodb_config_dict():
    """Get MongoDB config dictionary using the dynamic import helper"""
    return get_mongodb_config()[1]

def get_model_path():
    """Get model path using the dynamic import helper"""
    return get_model_config()[0]()

def get_model_config_dict():
    """Get model config dictionary using the dynamic import helper"""
    return get_model_config()[2]

def get_full_model_config():
    """Get complete model configuration using the dynamic import helper"""
    return get_model_config()[1]() 