from datetime import datetime

class ModuleStatus:
    def __init__(self):
        self.status = "stopped"
        self.last_update = None
        self.error_count = 0
        self.success_count = 0
        self.last_error = None

    def update(self, success=True, error=None):
        self.last_update = datetime.now()
        if success:
            self.status = "running"
            self.success_count += 1
        else:
            self.status = "error"
            self.error_count += 1
            self.last_error = str(error)

    def to_dict(self):
        return {
            "status": self.status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "last_error": self.last_error
        } 