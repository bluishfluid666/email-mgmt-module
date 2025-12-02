import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class UploadStatus(str, Enum):
    """Upload status enumeration"""
    PENDING = "pending"
    READING = "reading"
    ENCODING = "encoding"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadProgress:
    """Represents upload progress for a single file"""
    
    def __init__(self, upload_id: str, filename: str, total_size: int):
        self.upload_id = upload_id
        self.filename = filename
        self.total_size = total_size
        self.bytes_read = 0
        self.status = UploadStatus.PENDING
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert progress to dictionary"""
        progress_percent = (
            (self.bytes_read / self.total_size * 100) if self.total_size > 0 else 0
        )
        
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "status": self.status.value,
            "bytes_read": self.bytes_read,
            "total_size": self.total_size,
            "progress_percent": round(progress_percent, 2),
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class UploadProgressService:
    """Service for tracking file upload progress"""
    
    def __init__(self, cleanup_interval_seconds: int = 300):
        """
        Initialize upload progress service
        
        Args:
            cleanup_interval_seconds: Interval in seconds to clean up old progress records
        """
        self.progress: Dict[str, UploadProgress] = {}
        self.cleanup_interval = cleanup_interval_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old progress records"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_old_progress()
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # Event loop not running, cleanup will happen on next access
            pass
    
    def _cleanup_old_progress(self):
        """Remove progress records older than 1 hour"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        upload_ids_to_remove = [
            upload_id for upload_id, progress in self.progress.items()
            if progress.completed_at and progress.completed_at < cutoff_time
        ]
        
        for upload_id in upload_ids_to_remove:
            del self.progress[upload_id]
        
        if upload_ids_to_remove:
            logger.info(f"Cleaned up {len(upload_ids_to_remove)} old progress record(s)")
    
    def create_progress(self, filename: str, total_size: int) -> str:
        """
        Create a new progress tracker
        
        Args:
            filename: Name of the file being uploaded
            total_size: Total size of the file in bytes
            
        Returns:
            Upload ID for tracking progress
        """
        upload_id = str(uuid.uuid4())
        self.progress[upload_id] = UploadProgress(upload_id, filename, total_size)
        logger.info(f"Created progress tracker: {upload_id} for {filename} ({total_size} bytes)")
        return upload_id
    
    def update_progress(
        self,
        upload_id: str,
        bytes_read: Optional[int] = None,
        status: Optional[UploadStatus] = None,
        total_size: Optional[int] = None
    ):
        """
        Update upload progress
        
        Args:
            upload_id: Upload ID
            bytes_read: Number of bytes read so far
            status: Current status
            total_size: Total size (can be updated if initially unknown)
        """
        if upload_id not in self.progress:
            logger.warning(f"Progress tracker not found: {upload_id}")
            return
        
        progress = self.progress[upload_id]
        
        if bytes_read is not None:
            progress.bytes_read = bytes_read
        
        if total_size is not None:
            progress.total_size = total_size
        
        if status is not None:
            progress.status = status
        
        if status == UploadStatus.COMPLETED or status == UploadStatus.FAILED:
            progress.completed_at = datetime.now()
    
    def set_error(self, upload_id: str, error_message: str):
        """
        Mark upload as failed with error message
        
        Args:
            upload_id: Upload ID
            error_message: Error message
        """
        if upload_id not in self.progress:
            logger.warning(f"Progress tracker not found: {upload_id}")
            return
        
        progress = self.progress[upload_id]
        progress.status = UploadStatus.FAILED
        progress.error_message = error_message
        progress.completed_at = datetime.now()
    
    def get_progress(self, upload_id: str) -> Optional[Dict]:
        """
        Get current progress for an upload
        
        Args:
            upload_id: Upload ID
            
        Returns:
            Progress dictionary or None if not found
        """
        if upload_id not in self.progress:
            return None
        
        return self.progress[upload_id].to_dict()
    
    def delete_progress(self, upload_id: str):
        """
        Delete progress record
        
        Args:
            upload_id: Upload ID
        """
        if upload_id in self.progress:
            del self.progress[upload_id]
            logger.info(f"Deleted progress tracker: {upload_id}")


# Global upload progress service instance
upload_progress_service = UploadProgressService()

