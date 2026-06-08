"""
Content Management System
Manages all generated content with versioning and approval workflow.
Handles content storage, retrieval, and version tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional

from config import GeneratedContent, ContentVersion

class ContentManager:
    """
    Manages all generated content with versioning and approval workflow.
    Provides content storage, version tracking, and approval management.
    """
    
    def __init__(self):
        """Initialize content manager with empty storage."""
        self.content_store: Dict[str, GeneratedContent] = {}
        self.versions: Dict[str, List[ContentVersion]] = {}
        self.approvals: Dict[str, datetime] = {}
    
    def save_content(self, content_type: str, content: GeneratedContent, content_id: str = None) -> str:
        """
        Save content with versioning support.
        
        Args:
            content_type: Type of content (syllabus, lecture_notes, etc.)
            content: Generated content object
            content_id: Optional custom content ID
            
        Returns:
            Content ID for retrieval
        """
        if content_id is None:
            content_id = f"{content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if content_id not in self.versions:
            self.versions[content_id] = []
        
        version = ContentVersion(
            version_number=len(self.versions[content_id]) + 1,
            content=content.content,
            feedback="",
            approved=False,
            timestamp=content.timestamp
        )
        
        self.versions[content_id].append(version)
        self.content_store[content_id] = content
        
        return content_id
    
    def get_content(self, content_id: str) -> Optional[GeneratedContent]:
        """Retrieve content by ID."""
        return self.content_store.get(content_id)
    
    def get_versions(self, content_id: str) -> List[ContentVersion]:
        """Get all versions of content."""
        return self.versions.get(content_id, [])
    
    def get_latest_version(self, content_id: str) -> Optional[ContentVersion]:
        """Get the latest version of content."""
        versions = self.get_versions(content_id)
        return versions[-1] if versions else None
    
    def approve_content(self, content_id: str, feedback: str = "") -> bool:
        """Approve content version."""
        if content_id in self.versions and self.versions[content_id]:
            latest_version = self.versions[content_id][-1]
            latest_version.approved = True
            latest_version.feedback = feedback
            self.approvals[content_id] = datetime.now()
            return True
        return False
    
    def is_approved(self, content_id: str) -> bool:
        """Check if content is approved."""
        latest_version = self.get_latest_version(content_id)
        return latest_version.approved if latest_version else False
    
    def get_approval_date(self, content_id: str) -> Optional[datetime]:
        """Get approval date for content."""
        return self.approvals.get(content_id)
    
    def get_content_summary(self) -> Dict[str, Dict]:
        """Get summary of all stored content."""
        summary = {}
        
        for content_id, content in self.content_store.items():
            latest_version = self.get_latest_version(content_id)
            summary[content_id] = {
                "quality_score": content.quality_score,
                "version_count": len(self.versions.get(content_id, [])),
                "approved": latest_version.approved if latest_version else False,
                "created": content.timestamp.isoformat(),
                "last_modified": latest_version.timestamp.isoformat() if latest_version else content.timestamp.isoformat()
            }
        
        return summary
    
    def update_content(self, content_id: str, new_content: str, feedback: str = "") -> bool:
        """Update existing content with a new version."""
        if content_id in self.content_store:
            self.content_store[content_id].content = new_content
            self.content_store[content_id].version += 1
            
            version = ContentVersion(
                version_number=len(self.versions[content_id]) + 1,
                content=new_content,
                feedback=feedback,
                approved=False,
                timestamp=datetime.now()
            )
            
            self.versions[content_id].append(version)
            return True
        return False
    
    def delete_content(self, content_id: str) -> bool:
        """Delete content and all its versions."""
        deleted = False
        
        if content_id in self.content_store:
            del self.content_store[content_id]
            deleted = True
        
        if content_id in self.versions:
            del self.versions[content_id]
            deleted = True
        
        if content_id in self.approvals:
            del self.approvals[content_id]
        
        return deleted
    
    def get_content_types(self) -> List[str]:
        """Get list of content types in storage."""
        types = set()
        for content_id in self.content_store.keys():
            content_type = content_id.split('_')[0]
            types.add(content_type)
        return list(types)
