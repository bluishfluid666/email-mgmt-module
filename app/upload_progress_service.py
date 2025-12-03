import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
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
        self.upload_url: Optional[str] = None  # Microsoft Graph upload session URL
        self.draft_id: Optional[str] = None  # Draft ID for this upload
    
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
        self.draft_uploads: Dict[str, List[str]] = {}  # Map draft_id to list of upload_ids
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
    
    def create_progress(self, filename: str, total_size: int, draft_id: Optional[str] = None) -> str:
        """
        Create a new progress tracker
        
        Args:
            filename: Name of the file being uploaded
            total_size: Total size of the file in bytes
            draft_id: Optional draft ID to track uploads per draft
            
        Returns:
            Upload ID for tracking progress
        """
        upload_id = str(uuid.uuid4())
        progress = UploadProgress(upload_id, filename, total_size)
        progress.draft_id = draft_id
        self.progress[upload_id] = progress
        
        # Track upload by draft_id if provided
        if draft_id:
            if draft_id not in self.draft_uploads:
                self.draft_uploads[draft_id] = []
            self.draft_uploads[draft_id].append(upload_id)
        
        logger.info(f"Created progress tracker: {upload_id} for {filename} ({total_size} bytes)")
        return upload_id
    
    def set_upload_url(self, upload_id: str, upload_url: str):
        """
        Store the Microsoft Graph upload session URL for an upload
        
        Args:
            upload_id: Upload ID
            upload_url: Microsoft Graph upload session URL
        """
        if upload_id in self.progress:
            self.progress[upload_id].upload_url = upload_url
            logger.debug(f"Set upload URL for {upload_id}")
    
    def get_upload_url(self, upload_id: str) -> Optional[str]:
        """
        Get the Microsoft Graph upload session URL for an upload
        
        Args:
            upload_id: Upload ID
            
        Returns:
            Upload URL or None if not found
        """
        if upload_id in self.progress:
            return self.progress[upload_id].upload_url
        return None
    
    def get_pending_uploads_for_draft(self, draft_id: str) -> List[str]:
        """
        Get list of pending upload IDs for a draft
        
        Args:
            draft_id: Draft ID
            
        Returns:
            List of upload IDs that are not yet completed
        """
        if draft_id not in self.draft_uploads:
            return []
        
        pending = []
        for upload_id in self.draft_uploads.get(draft_id, []):
            if upload_id in self.progress:
                progress = self.progress[upload_id]
                if progress.status not in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                    pending.append(upload_id)
        
        return pending
    
    async def wait_for_uploads(self, draft_id: str, timeout: int = 300) -> bool:
        """
        Wait for all pending uploads for a draft to complete
        
        Args:
            draft_id: Draft ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all uploads completed, False if timeout
        """
        import time
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < timeout:
            pending = self.get_pending_uploads_for_draft(draft_id)
            if not pending:
                logger.info(f"All uploads completed for draft {draft_id}")
                return True
            
            # Check if any failed
            for upload_id in pending:
                if upload_id in self.progress:
                    progress = self.progress[upload_id]
                    if progress.status == UploadStatus.FAILED:
                        logger.warning(f"Upload {upload_id} failed for draft {draft_id}")
                        return False
                    # Auto-complete if bytes_read equals total_size (even if status isn't COMPLETED)
                    if progress.bytes_read >= progress.total_size and progress.total_size > 0:
                        logger.info(f"Auto-completing upload {upload_id} - all bytes uploaded ({progress.bytes_read}/{progress.total_size})")
                        self.update_progress(upload_id, status=UploadStatus.COMPLETED)
            
            check_count += 1
            if check_count % 10 == 0:  # Log every 5 seconds (10 * 0.5s)
                logger.info(f"Still waiting for {len(pending)} upload(s) for draft {draft_id}...")
            
            await asyncio.sleep(0.5)  # Check every 500ms
        
        # Timeout reached
        pending = self.get_pending_uploads_for_draft(draft_id)
        logger.warning(f"Timeout waiting for uploads for draft {draft_id}. Pending: {len(pending)}")
        return False
    
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

