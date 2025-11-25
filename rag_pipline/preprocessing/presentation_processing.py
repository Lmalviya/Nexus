from typing import List, Tuple
from langchain_core.documents import Document
from rag_pipline.preprocessing.extract import Extractor


class PresentationHandler:
    """Handler for PowerPoint and other presentation formats."""
    
    def __init__(self):
        self.extractor = Extractor()
    
    def process_presentation(self, file_path: str, user_id: str, org_id: str, use_ocr: bool = False) -> Tuple[List[Document], str]:
        """
        Process presentation file (PPT, PPTX) using Extractor (treats as PDF-like).
        
        Args:
            file_path: Path to presentation file
            user_id: User ID for database storage
            org_id: Organization ID for MinIO storage
            use_ocr: Whether to use OCR for text extraction
        
        Returns:
            Tuple[List[Document], str]: (documents, error_message)
        """
        try:
            # Use Extractor to process presentation (docling can handle PPTX)
            documents = self.extractor.extract(
                file_path=file_path,
                user_id=user_id,
                org_id=org_id,
                useOCR=use_ocr
            )
            
            if not documents:
                return [], "No content extracted from presentation"
            
            # Update metadata to reflect presentation type
            for doc in documents:
                doc.metadata['source_file_type'] = 'presentation'
                doc.metadata['original_extension'] = file_path.split('.')[-1]
            
            print(f"Successfully extracted {len(documents)} documents from presentation")
            return documents, ""
            
        except Exception as e:
            error_msg = f"Error processing presentation: {str(e)}"
            print(error_msg)
            return [], error_msg
