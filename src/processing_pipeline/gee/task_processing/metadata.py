from datetime import datetime


class GeeTaskProcessingMetadata:
    def __init__(self, task_id: str, user_id: str, aoi_id: str):
        self.task_id = task_id
        self.user_id = user_id
        self.aoi_id = aoi_id
        self.prepared_at = datetime.now()
        self.time_zone: str = ''
        self.aoi = None
