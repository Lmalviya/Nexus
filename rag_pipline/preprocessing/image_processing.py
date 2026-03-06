import os
import threading
from typing import List, Tuple
from langchain_core.documents import Document
from rag_pipline.utils.db_connection import ConnectionManager
from PIL import Image


class ImageHandler:
    """Handler for image files (PNG, JPG, JPEG, etc.)."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
    
    def _upload_image(self, user_id: str, org_id: str, image_path: str, image_name: str):
        """Upload image to MinIO."""
        try:
            self.connection_manager.get_minio().push(org_id, user_id, "images", image_path, image_name)
            print(f"Image {image_name} uploaded asynchronously.")
        except Exception as e:
            print(f"Error uploading image {image_name}: {e}")
    
    def _validate_image(self, file_path: str) -> Tuple[bool, str]:
        """Validate image file."""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if os.path.getsize(file_path) == 0:
            return False, "Image file is empty"
        
        # Try to open with PIL to validate
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True, ""
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    def process_image(self, file_path: str, user_id: str, org_id: str) -> Tuple[List[Document], str]:
        """
        Process image file and upload to MinIO.
        
        Args:
            file_path: Path to image file
            user_id: User ID
            org_id: Organization ID for MinIO storage
        
        Returns:
            Tuple[List[Document], str]: (documents, error_message)
        """
        # Validate image
        is_valid, error_msg = self._validate_image(file_path)
        if not is_valid:
            print(f"Image validation failed: {error_msg}")
            return [], error_msg
        
        try:
            # Get image info
            file_name = os.path.basename(file_path)
            file_ext = file_path.split('.')[-1].lower()
            
            # Get image dimensions
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
            
            # Upload to MinIO asynchronously
            t = threading.Thread(target=self._upload_image, args=(user_id, org_id, file_path, file_name))
            t.start()
            
            # Create LangChain document
            doc = Document(
                page_content="",  # Images don't have text content
                metadata={
                    "source": file_path,
                    "content_type": "image",
                    "source_file_type": file_ext,
                    "image_name": file_name,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "local_path": os.path.abspath(file_path),
                    "storage_location": f"org-{org_id}/user_{user_id}/images/{file_name}"
                }
            )
            
            print(f"Successfully processed image: {file_name}")
            return [doc], ""
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            print(error_msg)
            return [], error_msg
