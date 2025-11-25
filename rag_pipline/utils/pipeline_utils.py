"""Utility functions for the document processing pipeline."""

import uuid
import os
import re
from typing import Dict, Tuple, Optional
from langchain_core.documents import Document
from urllib.parse import urlparse


def parse_minio_url(url: str) -> Dict[str, str]:
    """
    Parse MinIO URL to extract components.
    
    Expected format: minio://bucket/org_id/user_id/category/object_name
    or: http://localhost:9000/bucket/org_id/user_id/category/object_name
    
    Args:
        url: MinIO URL
        
    Returns:
        Dictionary with bucket, org_id, user_id, category, object_name
    """
    # Handle both minio:// and http:// URLs
    if url.startswith('minio://'):
        url = url.replace('minio://', '')
        parts = url.split('/')
    elif url.startswith('http://') or url.startswith('https://'):
        parsed = urlparse(url)
        # Remove leading slash and split
        parts = parsed.path.lstrip('/').split('/')
    else:
        raise ValueError(f"Invalid MinIO URL format: {url}")
    
    if len(parts) < 5:
        raise ValueError(f"MinIO URL must have at least 5 parts (bucket/org/user/category/object): {url}")
    
    return {
        'bucket': parts[0],
        'org_id': parts[1],
        'user_id': parts[2],
        'category': parts[3],
        'object_name': '/'.join(parts[4:])  # Handle nested paths
    }


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def extract_file_info(file_path: str) -> Dict[str, str]:
    """
    Extract file metadata from file path.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    return {
        'file_name': file_name,
        'file_extension': file_ext,
        'file_size': file_size,
        'file_path': os.path.abspath(file_path),
    }


def is_text_content(document: Document) -> bool:
    """
    Check if document contains text or table content.
    
    Args:
        document: LangChain Document
        
    Returns:
        True if text/table content
    """
    content_type = document.metadata.get('content_type', 'text')
    return content_type in ['text', 'table']


def is_image_content(document: Document) -> bool:
    """
    Check if document contains image content.
    
    Args:
        document: LangChain Document
        
    Returns:
        True if image content
    """
    content_type = document.metadata.get('content_type', 'text')
    return content_type == 'image'


def build_minio_url(bucket: str, org_id: str, user_id: str, category: str, object_name: str) -> str:
    """
    Build MinIO URL from components.
    
    Args:
        bucket: Bucket name
        org_id: Organization ID
        user_id: User ID
        category: Category (e.g., 'images', 'documents')
        object_name: Object name
        
    Returns:
        MinIO URL string
    """
    return f"minio://{bucket}/{org_id}/{user_id}/{category}/{object_name}"


def sanitize_collection_name(name: str) -> str:
    """
    Sanitize collection name for Qdrant.
    
    Qdrant collection names must:
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, and hyphens
    - Be between 1 and 255 characters
    
    Args:
        name: Collection name
        
    Returns:
        Sanitized collection name
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    
    # Truncate to 255 characters
    sanitized = sanitized[:255]
    
    return sanitized


def get_collection_names(user_id: str) -> Tuple[str, str]:
    """
    Get collection names for text and image embeddings.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (text_collection_name, image_collection_name)
    """
    sanitized_user_id = sanitize_collection_name(user_id)
    text_collection = f"{sanitized_user_id}_text_embeddings"
    image_collection = f"{sanitized_user_id}_image_embeddings"
    
    return text_collection, image_collection
