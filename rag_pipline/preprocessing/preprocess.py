import hashlib
import os
from typing import List, Tuple
from langchain_core.documents import Document
from rag_pipline.preprocessing.pdf_processing import PDFHandler
from rag_pipline.preprocessing.spreadsheet_processing import SpreadsheetHandler
from rag_pipline.preprocessing.presentation_processing import PresentationHandler
from rag_pipline.preprocessing.image_processing import ImageHandler


class FilePreprocessor:
    """Main file preprocessor that routes files to appropriate handlers."""
    
    def __init__(self):
        self.hasher = hashlib.md5()
        
        # Initialize handlers
        self.pdf_handler = None  # Lazy initialization
        self.spreadsheet_handler = None
        self.presentation_handler = None
        self.image_handler = None

    def check_file_hash_in_db(self, file_hash: str) -> bool:
        """Check if file hash exists in database (to be implemented)."""
        # TODO: Implement database check
        pass

    def compute_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def is_file_available(self, file_path: str) -> bool:
        """Check if file has already been processed."""
        file_hash = self.compute_hash(file_path)
        return self.check_file_hash_in_db(file_hash)
        
    def get_file_extension(self, file_path: str) -> str:
        """Get file extension in lowercase."""
        return file_path.split('.')[-1].lower()
    
    def get_file_type(self, file_path: str) -> str:
        """
        Determine file type category.
        
        Returns:
            'pdf', 'spreadsheet', 'presentation', 'image', 'text', or 'unsupported'
        """
        ext = self.get_file_extension(file_path)
        
        # PDF files
        if ext == 'pdf':
            return 'pdf'
        
        # Spreadsheet files
        elif ext in ['csv', 'xlsx', 'xls', 'xlsm', 'xlsb', 'ods', 'tsv']:
            return 'spreadsheet'
        
        # Presentation files
        elif ext in ['ppt', 'pptx', 'odp']:
            return 'presentation'
        
        # Image files
        elif ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'svg']:
            return 'image'
        
        # Text files (to be implemented later)
        elif ext in ['txt', 'py', 'html', 'xml', 'json', 'md', 'rst']:
            return 'text'
        
        else:
            return 'unsupported'

    def preprocess(self, file_path: str, user_id: str, org_id: str, use_ocr: bool = False) -> Tuple[List[Document], str]:
        """
        Preprocess file and return LangChain documents.
        
        Args:
            file_path: Path to file
            user_id: User ID for database storage
            org_id: Organization ID for MinIO storage
            use_ocr: Whether to use OCR for text extraction (PDF/presentations)
        
        Returns:
            Tuple[List[Document], str]: (documents, error_message)
        """
        # Validate file exists
        if not os.path.exists(file_path):
            return []
        
        # Determine file type
        file_type = self.get_file_type(file_path)
        
        try:
            # Route to appropriate handler
            if file_type == 'pdf':
                if self.pdf_handler is None:
                    self.pdf_handler = PDFHandler(file_path)
                else:
                    self.pdf_handler.file_path = file_path
                return self.pdf_handler.process_pdf(user_id, org_id, use_ocr)
            
            elif file_type == 'spreadsheet':
                if self.spreadsheet_handler is None:
                    self.spreadsheet_handler = SpreadsheetHandler()
                return self.spreadsheet_handler.process_spreadsheet(file_path, user_id, org_id)
            
            elif file_type == 'presentation':
                if self.presentation_handler is None:
                    self.presentation_handler = PresentationHandler()
                return self.presentation_handler.process_presentation(file_path, user_id, org_id, use_ocr)
            
            elif file_type == 'image':
                if self.image_handler is None:
                    self.image_handler = ImageHandler()
                return self.image_handler.process_image(file_path, user_id, org_id)
            
            elif file_type == 'text':
                # Text files - to be implemented later
                with open(file_path, 'r') as f:
                    content = f.read()
                data = [
                    Document(
                        page_content=content, 
                        metadata={
                            "source": file_path, 
                            "content_type": "text", 
                            "file_type": str(file_path.split('.')[-1].lower()),
                            }
                        )
                ]
                return data
            
            else:
                return []
        
        except Exception as e:
            error_msg = f"Error preprocessing file: {str(e)}"
            print(error_msg)
            return []