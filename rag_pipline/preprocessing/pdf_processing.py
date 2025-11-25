import pypdf
import os
from typing import List, Tuple
from langchain_core.documents import Document
from rag_pipline.preprocessing.extract import Extractor


class PDFHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.extractor = Extractor()

    def is_password_protected(self) -> bool:
        """Check if PDF is password protected or encrypted."""
        try:
            reader = pypdf.PdfReader(self.file_path)
            return reader.is_encrypted
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return True

    def is_valid_pdf(self) -> Tuple[bool, str]:
        """
        Validate PDF file before processing.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(self.file_path):
            return False, "File does not exist"
        
        # Check file extension
        if not self.file_path.lower().endswith('.pdf'):
            return False, "File is not a PDF"
        
        # Check if file is empty
        if os.path.getsize(self.file_path) == 0:
            return False, "PDF file is empty"
        
        # Check if password protected
        if self.is_password_protected():
            return False, "PDF is password protected or encrypted"
        
        # Try to read basic PDF structure
        try:
            reader = pypdf.PdfReader(self.file_path)
            if len(reader.pages) == 0:
                return False, "PDF has no pages"
        except pypdf.errors.PdfReadError as e:
            return False, f"PDF is corrupted or invalid: {str(e)}"
        except Exception as e:
            return False, f"Error validating PDF: {str(e)}"
        
        return True, ""

    def process_pdf(self, user_id: str, org_id: str, use_ocr: bool = False) -> Tuple[List[Document], str]:
        """
        Process PDF file and extract content using Extractor.
        
        Args:
            user_id: User ID for database storage
            org_id: Organization ID for MinIO storage
            use_ocr: Whether to use OCR for text extraction
        
        Returns:
            Tuple[List[Document], str]: (documents, error_message)
        """
        # Validate PDF first
        is_valid, error_msg = self.is_valid_pdf()
        if not is_valid:
            print(f"PDF validation failed: {error_msg}")
            return [], error_msg
        
        # Extract content using Extractor
        try:
            documents = self.extractor.extract(
                file_path=self.file_path,
                user_id=user_id,
                org_id=org_id,
                useOCR=use_ocr
            )
            
            if not documents:
                return [], "No content extracted from PDF"
            
            print(f"Successfully extracted {len(documents)} documents from PDF")
            return documents, ""
            
        except Exception as e:
            error_msg = f"Error processing PDF with docling: {str(e)}"
            print(error_msg)
            return [], error_msg

    def get_pdf_metadata(self) -> dict:
        """
        Extract metadata from PDF.
        
        Returns:
            dict: PDF metadata (title, author, pages, etc.)
        """
        try:
            reader = pypdf.PdfReader(self.file_path)
            metadata = {
                'num_pages': len(reader.pages),
                'title': reader.metadata.get('/Title', 'Unknown') if reader.metadata else 'Unknown',
                'author': reader.metadata.get('/Author', 'Unknown') if reader.metadata else 'Unknown',
                'subject': reader.metadata.get('/Subject', 'Unknown') if reader.metadata else 'Unknown',
                'creator': reader.metadata.get('/Creator', 'Unknown') if reader.metadata else 'Unknown',
                'producer': reader.metadata.get('/Producer', 'Unknown') if reader.metadata else 'Unknown',
                'is_encrypted': reader.is_encrypted,
                'file_size_mb': round(os.path.getsize(self.file_path) / (1024 * 1024), 2)
            }
            return metadata
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}