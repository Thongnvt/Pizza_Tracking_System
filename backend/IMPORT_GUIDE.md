# Flexible Import Guide for MongoDB Configuration

## Problem
The MongoDB configuration needs to be imported differently depending on the execution context:

- **GUI/Tkinter context**: `from ..config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG`
- **Local frontend context**: `from config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG`

## Solution
We've created a flexible import helper that automatically handles both scenarios.

## Files Created/Modified

### 1. `backend/utils/import_helper.py`
This is the main helper module that handles the dual import scenario.

**Key Features:**
- Tries relative import first (for GUI context)
- Falls back to absolute import (for frontend context)
- Dynamic path resolution as additional fallback
- File-based import as last resort

**Usage:**
```python
from utils.import_helper import get_mongodb_uri, get_mongodb_config_dict

# Get MongoDB URI
uri = get_mongodb_uri()

# Get MongoDB config dictionary
config = get_mongodb_config_dict()
```

### 2. `backend/utils/feedback_storage.py` (Modified)
Updated to use the new import helper:

**Before:**
```python
from ..config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
```

**After:**
```python
from .import_helper import get_mongodb_uri, get_mongodb_config_dict
```

### 3. `backend/example_usage.py`
Example script demonstrating how to use the flexible import approach.

## How It Works

The `import_helper.py` module uses a multi-layered approach:

1. **Relative Import**: Tries `from ..config.mongodb_config import ...`
2. **Absolute Import**: Tries `from config.mongodb_config import ...`
3. **Path Manipulation**: Adds backend directory to sys.path and tries again
4. **File-based Import**: Uses `importlib.util` to load the module directly from file

## Usage Examples

### In GUI/Tkinter Applications
```python
from utils.import_helper import get_mongodb_uri, get_mongodb_config_dict

# The helper automatically uses the correct import method
uri = get_mongodb_uri()
config = get_mongodb_config_dict()
```

### In Local Frontend Applications
```python
from utils.import_helper import get_mongodb_uri, get_mongodb_config_dict

# Same code, different execution context
uri = get_mongodb_uri()
config = get_mongodb_config_dict()
```

### In Other Modules
```python
from utils.import_helper import get_mongodb_uri, get_mongodb_config_dict

class MyClass:
    def __init__(self):
        self.uri = get_mongodb_uri()
        self.config = get_mongodb_config_dict()
```

## Testing

Run the example script to test the import functionality:

```bash
cd backend
python example_usage.py
```

This will test all import scenarios and show which ones work in your current environment.

## Benefits

1. **Single Codebase**: No need to maintain different import statements
2. **Automatic Detection**: Works regardless of execution context
3. **Robust Fallbacks**: Multiple fallback mechanisms ensure it works
4. **Easy Migration**: Simple to update existing code
5. **Future-Proof**: Handles new execution contexts automatically

## Migration Guide

To migrate existing code:

1. **Replace imports:**
   ```python
   # Old
   from ..config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
   # or
   from config.mongodb_config import get_mongodb_uri, MONGODB_CONFIG
   
   # New
   from utils.import_helper import get_mongodb_uri, get_mongodb_config_dict
   ```

2. **Update variable names:**
   ```python
   # Old
   uri = get_mongodb_uri()
   config = MONGODB_CONFIG
   
   # New
   uri = get_mongodb_uri()
   config = get_mongodb_config_dict()
   ```

## Troubleshooting

If you encounter import errors:

1. **Check file paths**: Ensure `mongodb_config.py` exists in `backend/config/`
2. **Verify Python path**: Make sure the backend directory is in your Python path
3. **Run example script**: Use `example_usage.py` to test your environment
4. **Check permissions**: Ensure Python can read the config files

## Notes

- The helper is designed to be lightweight and fast
- It caches successful imports for better performance
- Error messages are descriptive to help with debugging
- The approach is extensible for other configuration modules

---

# Flexible Model Configuration Guide

## Problem
The YOLO model path was hardcoded in the detection handler:
```python
self.model = YOLO('D:/Counting System/backend/models/best.pt')
```

This caused issues when running in different contexts or on different systems.

## Solution
We've created a flexible model configuration system that automatically handles different execution contexts.

## Files Created/Modified

### 1. `backend/config/model_config.py`
New model configuration module with flexible path resolution.

**Key Features:**
- Multiple path strategies for different execution contexts
- Automatic model path validation
- Configurable model parameters
- Class name and tracking class configuration

### 2. `backend/utils/import_helper.py` (Extended)
Extended to include model configuration functions.

**New Functions:**
```python
from utils.import_helper import get_model_path, get_model_config_dict, get_full_model_config

# Get model path
model_path = get_model_path()

# Get model configuration
config = get_full_model_config()
```

### 3. `backend/utils/detection_handler.py` (Modified)
Updated to use flexible model configuration.

**Before:**
```python
self.model = YOLO('D:/Counting System/backend/models/best.pt')
self.conf_threshold = 0.5
self.class_names = {0: 'pizza', 1: 'box_open', 2: 'box_close', 3: 'box_nilon'}
```

**After:**
```python
from .import_helper import get_model_path, get_full_model_config

self.model_config = get_full_model_config()
self.model_path = get_model_path()
self.model = YOLO(self.model_path)
self.conf_threshold = self.model_config['confidence_threshold']
self.class_names = self.model_config['classes']
self.tracking_classes = self.model_config['tracking_classes']
```

### 4. `backend/test_model_config.py`
Test script to verify the flexible model configuration works correctly.

## Model Configuration

The model configuration includes:

```python
MODEL_CONFIG = {
    'default_model': 'best.pt',
    'model_type': 'yolo',
    'confidence_threshold': 0.5,
    'iou_threshold': 0.45,
    'device': 'auto',
    'classes': {
        0: 'pizza',
        1: 'box_open',
        2: 'box_close',
        3: 'box_nilon'
    },
    'tracking_classes': [1, 2],  # Classes to track
    'model_paths': {
        'relative': 'backend/models/best.pt',
        'absolute': 'D:/Counting System/backend/models/best.pt',
        'sfsort': 'SFSORT/best.pt'
    }
}
```

## Path Resolution Strategy

The system tries multiple path strategies in order:

1. **Relative to current working directory**
2. **Absolute path** (for GUI context)
3. **Relative to backend directory**
4. **Relative to project root**
5. **SFSORT directory**

## Usage Examples

### Basic Model Loading
```python
from utils.import_helper import get_model_path, get_full_model_config

# Get model path
model_path = get_model_path()

# Get complete configuration
config = get_full_model_config()

# Load model
from ultralytics import YOLO
model = YOLO(model_path)
```

### In DetectionHandler
```python
from utils.detection_handler import DetectionHandler

# The handler automatically uses flexible model configuration
handler = DetectionHandler()
print(f"Model path: {handler.model_path}")
print(f"Tracking classes: {handler.tracking_classes}")
```

## Testing

Run the model configuration test:

```bash
cd backend
python test_model_config.py
```

This will test:
- Model path resolution
- Configuration loading
- DetectionHandler initialization
- Actual model loading

## Benefits

1. **Flexible Paths**: Works in any execution context
2. **Easy Configuration**: Centralized model settings
3. **Automatic Validation**: Checks if model files exist
4. **Extensible**: Easy to add new model types or parameters
5. **Consistent**: Same approach as MongoDB configuration

## Migration Guide

To migrate existing code that uses hardcoded model paths:

1. **Replace hardcoded paths:**
   ```python
   # Old
   model = YOLO('D:/Counting System/backend/models/best.pt')
   
   # New
   from utils.import_helper import get_model_path
   model = YOLO(get_model_path())
   ```

2. **Use configuration for parameters:**
   ```python
   # Old
   conf_threshold = 0.5
   class_names = {0: 'pizza', 1: 'box_open', 2: 'box_close', 3: 'box_nilon'}
   
   # New
   from utils.import_helper import get_full_model_config
   config = get_full_model_config()
   conf_threshold = config['confidence_threshold']
   class_names = config['classes']
   ```

## Troubleshooting

If you encounter model loading issues:

1. **Check model file exists**: Verify `best.pt` is in the expected location
2. **Run test script**: Use `test_model_config.py` to diagnose issues
3. **Check paths**: Ensure the model file is in one of the expected directories
4. **Verify permissions**: Make sure Python can read the model file 