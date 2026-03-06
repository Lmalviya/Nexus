import os
import shutil
import io
import base64
from typing import List, Dict, Tuple, Optional
from enum import Enum
from langchain_core.documents import Document
from PIL import Image

from rag_pipline.preprocessing.preprocess import FilePreprocessor
from rag_pipline.chunking import ChunkingFactory
from rag_pipline.utils.embeddings import TextEmbeddings, ImageEmbeddings
from rag_pipline.utils.db_connection import ConnectionManager
from rag_pipline.utils.llm_call import generate_description
from rag_pipline.utils.pipeline_utils import (
    parse_minio_url,
    generate_unique_id,
    extract_file_info,
    is_text_content,
    is_image_content,
    build_minio_url,
    get_collection_names
)
from rag_pipline.config import TextEmbeddingsConfig, ImageEmbeddingsConfig
from rag_pipline.pipeline_config import PipelineConfig

class DocumentType(Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    PDF = "pdf"

class DocumentPipeline:
    """
    End-to-end document processing pipeline.
    
    Handles downloading, preprocessing, chunking, embedding generation,
    and storage in Qdrant vector database.
    """
    
    def __init__(self, config: PipelineConfig = None):
        """
        Initialize the pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()

        self.batch_size = 100
        self.text_chunking_type = 'sentence'
        
        # Initialize components
        self.connection_manager = ConnectionManager()
        self.preprocessor = FilePreprocessor()
        self.chunking_factory = ChunkingFactory()
        self.text_embedder = TextEmbeddings(TextEmbeddingsConfig())
        self.image_embedder = ImageEmbeddings(ImageEmbeddingsConfig(), device=self.config.device)
        
        # Create temp directory
        os.makedirs(self.config.temp_dir, exist_ok=True)
    
    def process_document(self, minio_url: str, user_id: str, org_id: str, use_ocr: bool = False) -> Dict[str, any]:
        """
        Process a document from MinIO URL.
        
        Args:
            minio_url: MinIO URL of the document
            user_id: User ID
            org_id: Organization ID
            use_ocr: Whether to use OCR for text extraction
            
        Returns:
            Dictionary with processing results
        """
        print(f"Processing document: {minio_url}")
        
        # Step 1: Download from MinIO
        local_file_path = self._download_from_minio(minio_url, org_id, user_id)
        if not local_file_path:
            return {"success": False, "error": "Failed to download file from MinIO"}
        
        try:
            # Step 2: Preprocess document
            print("Preprocessing document...")
            documents, error = self.preprocessor.preprocess(local_file_path, user_id, org_id, use_ocr)
            
            if error:
                return {"success": False, "error": error}
            
            if not documents:
                return {"success": False, "error": "No content extracted from document"}
            
            # Step 3: Separate text and image content
            print("Separating content types...")
            text_docs, image_docs = self._separate_content(documents)
            
            # Step 4: Process text content
            text_results = {}
            if text_docs:
                print(f"Processing {len(text_docs)} text/table documents...")
                text_results = self._process_text_content(text_docs, user_id, minio_url)
            
            # Step 5: Process image content
            image_results = {}
            if image_docs:
                print(f"Processing {len(image_docs)} images...")
                image_results = self._process_image_content(image_docs, user_id, org_id, minio_url)
            
            # Step 6: Cleanup
            if self.config.cleanup_temp_files:
                self._cleanup(local_file_path)
            
            return {
                "success": True,
                "text_chunks_stored": text_results.get("chunks_stored", 0) + image_results.get("image_descriptions_stored", 0),
                "images_stored": image_results.get("images_stored", 0),
                "text_collection": text_results.get("collection_name"),
                "image_collection": image_results.get("image_collection_name"),
            }
        
        except Exception as e:
            print(f"Error processing document: {e}") 
            if self.config.cleanup_temp_files:
                self._cleanup(local_file_path)
            return {"success": False, "error": str(e)}
    
    def _download_from_minio(self, minio_url: str, org_id: str, user_id: str) -> Optional[str]:
        """
        Download file from MinIO.
        
        Args:
            minio_url: MinIO URL
            org_id: Organization ID
            user_id: User ID
            
        Returns:
            Local file path or None if failed
        """
        try:
            # Parse MinIO URL
            url_parts = parse_minio_url(minio_url)
            
            # Generate local file path
            local_filename = url_parts['object_name'].replace('/', '_')
            local_path = os.path.join(self.config.temp_dir, local_filename)
            
            # Download from MinIO
            self.connection_manager.get_minio().pull(
                org_id=url_parts['org_id'],
                user_id=url_parts['user_id'],
                category=url_parts['category'],
                object_name=url_parts['object_name'],
                file_path=local_path
            )
            
            return local_path
        
        except Exception as e:
            print(f"Error downloading from MinIO: {e}")
            return None
    
    def _separate_content(self, documents: List[Document]) -> Tuple[List[Document], List[Document]]:
        """
        Separate text/table content from images.
        
        Args:
            documents: List of documents
            
        Returns:
            Tuple of (text_docs, image_docs)
        """
        text_docs = []
        image_docs = []
        
        for doc in documents:
            if is_text_content(doc):
                # Only include if has content
                if doc.page_content and doc.page_content.strip():
                    text_docs.append(doc)
            elif is_image_content(doc):
                image_docs.append(doc)
        
        return text_docs, image_docs
    
    def _process_text_content(self, text_docs: List[Document], user_id: str, minio_url: str) -> Dict[str, any]:
        """
        Process text content: chunk and embed.
        
        Args:
            text_docs: List of text documents
            user_id: User ID
            minio_url: Original MinIO URL
            
        Returns:
            Processing results
        """
        # Step 1: Chunk text content
        print("Chunking text content...")
        all_chunks = []
        
        for doc in text_docs:
            # Determine chunking strategy based on content type
            content_type = doc.metadata.get('content_type', 'text')
            
            if content_type == DocumentType.TABLE:
                # Keep table description as a single chunk
                chunks = [Document(page_content=doc.page_content, metadata=doc.metadata)]
            elif content_type == DocumentType.TEXT:
                # Use semantic chunking for regular text
                chunks = self.chunking_factory.chunk_text(
                    doc.page_content,
                    chunker_type=self.text_chunking_type,
                    metadata=doc.metadata
                )
            else:
                raise ValueError(f"Unknown content type: {content_type}")
            
            all_chunks.extend(chunks)
        
        if not all_chunks:
            return {"chunks_stored": 0}
        
        print(f"Generated {len(all_chunks)} chunks")
        
        # Step 2: Generate embeddings
        print("Generating text embeddings...")
        chunk_texts = [chunk.page_content for chunk in all_chunks]
        embeddings = self.text_embedder.embed_documents(chunk_texts)
        
        # Step 3: Prepare metadata
        payloads = []
        for i, chunk in enumerate(all_chunks):
            payload = chunk.metadata.copy()
            payload["type"] = DocumentType.TEXT
            payload['chunk_id'] = generate_unique_id('chunk')
            payload['minio_url'] = minio_url
            payload['chunk_text'] = chunk.page_content
            payloads.append(payload)
        
        # Step 4: Create collection and store embeddings
        print("Storing text embeddings in Qdrant...")
        qdrant = self.connection_manager.get_qdrant()
        collection_name = qdrant.create_text_collection(user_id, self.config.text_embedding_dim)
        
        # Store in batches
        for i in range(0, len(embeddings), self.batch_size):
            batch_embeddings = embeddings[i:i + self.batch_size]
            batch_payloads = payloads[i:i + self.batch_size]
            qdrant.push_text_embeddings(user_id, batch_embeddings, batch_payloads)
        
        return {
            "chunks_stored": len(all_chunks),
            "collection_name": collection_name
        }
    
    def _process_image_content(self, image_docs: List[Document], user_id: str, org_id: str, minio_url: str) -> Dict[str, any]:
        """
        Process image content: load images and embed.
        
        Args:
            image_docs: List of image documents
            user_id: User ID
            org_id: Organization ID
            minio_url: Original MinIO URL
            
        Returns:
            Processing results
        """
        # Step 1: Load images
        print("Loading images...")
        user_images = []
        pdf_images = []
        valid_image_docs = []
        valid_pdf_image_docs = []
        for doc in image_docs:
            local_path = doc.metadata.get('local_path')
            if local_path and os.path.exists(local_path):
                try:
                    img = Image.open(local_path).convert('RGB')
                    if doc.metadata.get('source_file_type') != DocumentType.PDF:
                        user_images.append(img)
                        valid_image_docs.append(doc)
                    elif doc.metadata.get('source_file_type') == DocumentType.PDF:
                        pdf_images.append(img)
                        valid_pdf_image_docs.append(doc)
                    else:
                        raise ValueError(f"Unknown source file type: {doc.metadata.get('source_file_type')}")
                except Exception as e:
                    print(f"Error loading image {local_path}: {e}")
        
        if not user_images and not pdf_images:
            return {"images_stored": 0}
        
        print(f"Loaded {len(user_images)} user images and {len(pdf_images)} pdf images")
        
        # Step 2: Generate embeddings and descriptions
        print("Generating image embeddings...")
        user_image_embeddings = []
        if user_images:
            user_image_embeddings = self.image_embedder.embed_images(user_images)
        
        # Generate descriptions for PDF images
        image_descriptions = []
        if pdf_images:
            print(f"Generating descriptions for {len(pdf_images)} PDF images...")
            for img in pdf_images:
                # Convert PIL image to base64
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # Call LLM to describe image
                desc = generate_description(
                    content_type="image",
                    data={"image_data": img_str},
                    session_id=f"desc_{user_id}_{generate_unique_id('desc')}"
                )
                image_descriptions.append(desc)
        
        pdf_image_descriptions_embeddings = []
        if image_descriptions:
            pdf_image_descriptions_embeddings = self.text_embedder.embed_documents(image_descriptions)
        
        # Step 3: Prepare metadata
        image_payloads = []
        for i, doc in enumerate(valid_image_docs):
            payload = doc.metadata.copy()
            payload["type"] = DocumentType.IMAGE
            payload['image_id'] = generate_unique_id('image')
            payload['source_minio_url'] = minio_url
            
            # Get MinIO URL for the image itself
            local_path = doc.metadata.get('local_path', '')
            image_filename = os.path.basename(local_path)
            payload['image_minio_url'] = build_minio_url(
                f"org-{org_id}",
                org_id, 
                user_id,
                "images",
                image_filename
            )
            image_payloads.append(payload)
        
        pdf_image_payload = []
        for i, doc in enumerate(valid_pdf_image_docs):
            payload = doc.metadata.copy()
            payload["type"] = DocumentType.PDF
            payload['image_id'] = generate_unique_id('image')
            payload['source_minio_url'] = minio_url
            payload['description'] = image_descriptions[i] if i < len(image_descriptions) else ""
            
            # Get MinIO URL for the image itself
            local_path = doc.metadata.get('local_path', '')
            pdf_image_filename = os.path.basename(local_path)
            payload['image_minio_url'] = build_minio_url(
                f"org-{org_id}",
                org_id, 
                user_id,
                "images",
                pdf_image_filename
            )
            pdf_image_payload.append(payload)
        
        # Step 4: Create collection and store embeddings
        print("Storing image embeddings in Qdrant...")
        qdrant = self.connection_manager.get_qdrant()
        image_collection_name = qdrant.create_image_collection(user_id, self.config.image_embedding_dim)
        text_collection_name = qdrant.create_text_collection(user_id, self.config.text_embedding_dim)

        # Store user images (image embeddings)
        if user_image_embeddings and image_payloads:
            for i in range(0, len(image_payloads), self.batch_size):
                batch_embeddings = user_image_embeddings[i:i + self.batch_size]
                batch_payloads = image_payloads[i:i + self.batch_size]
                qdrant.push_image_embeddings(user_id, batch_embeddings, batch_payloads, image_collection_name)
        
        # Store PDF images (text embeddings of descriptions)
        if pdf_image_descriptions_embeddings and pdf_image_payload:
            for i in range(0, len(pdf_image_payload), self.batch_size):
                batch_embeddings = pdf_image_descriptions_embeddings[i:i + self.batch_size]
                batch_payloads = pdf_image_payload[i:i + self.batch_size]
                qdrant.push_text_embeddings(user_id, batch_embeddings, batch_payloads, text_collection_name)
        
        return {
            "images_stored": len(image_payloads),
            "image_descriptions_stored": len(pdf_image_payload),
            "image_collection_name": image_collection_name,
            "text_collection_name": text_collection_name
        }
    
    def _cleanup(self, file_path: str):
        """
        Clean up temporary files.
        
        Args:
            file_path: Path to file to clean up
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            
            # Also clean up any temp image files
            temp_dir = os.path.dirname(file_path)
            for filename in os.listdir(temp_dir):
                if filename.startswith('temp_image_'):
                    temp_file = os.path.join(temp_dir, filename)
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
