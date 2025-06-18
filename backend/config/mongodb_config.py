# MongoDB Configuration
MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'username': '',  
    'password': '',  
    'database': 'pizza_detection_feedback',
    'collections': {
        'feedback': 'detection_feedback',
        'metrics': 'model_metrics'
    }
}

def get_mongodb_uri():
    """Get MongoDB connection URI"""
    if MONGODB_CONFIG['username'] and MONGODB_CONFIG['password']:
        return f"mongodb://{MONGODB_CONFIG['username']}:{MONGODB_CONFIG['password']}@{MONGODB_CONFIG['host']}:{MONGODB_CONFIG['port']}"
    return f"mongodb://{MONGODB_CONFIG['host']}:{MONGODB_CONFIG['port']}" 