import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from langchain_core.documents import Document
from .base_chunker import BaseChunker


class StructureChunker(BaseChunker):
    """
    Structure-aware chunking for JSON and XML files.
    
    This chunker:
    1. Parses JSON/XML structure
    2. Extracts top-level objects/elements as chunks
    3. For large objects, recursively chunks nested structures
    4. Preserves parent context in metadata
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Configuration
        self.max_chunk_size = self.config.get('max_chunk_size', 1000)
        self.preserve_structure = self.config.get('preserve_structure', True)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk structured data (JSON/XML).
        
        Args:
            content: The structured content to chunk
            metadata: Optional metadata (should include 'file_type' key)
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        file_type = metadata.get('file_type', 'json').lower()
        
        if file_type == 'json':
            return self._chunk_json(content, metadata)
        elif file_type == 'xml':
            return self._chunk_xml(content, metadata)
        else:
            # Fallback to treating as text
            return [self._create_document(content, metadata)]
    
    def _chunk_json(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        Chunk JSON content.
        
        Args:
            content: JSON string
            metadata: Metadata for chunks
            
        Returns:
            List of Document objects
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            # If parsing fails, return as single chunk with error
            chunk_metadata = metadata.copy()
            chunk_metadata['parse_error'] = str(e)
            return [self._create_document(content, chunk_metadata)]
        
        chunks = []
        
        if isinstance(data, dict):
            # Chunk dictionary by top-level keys
            for key, value in data.items():
                chunk_data = {key: value}
                chunk_text = json.dumps(chunk_data, indent=2)
                
                # If chunk is too large, recursively chunk it
                if self._count_tokens(chunk_text) > self.max_chunk_size:
                    sub_chunks = self._chunk_json_recursive(value, [key], metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': len(chunks),
                        'path': key,
                        'type': type(value).__name__,
                        'chunking_method': 'structure',
                    })
                    chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        elif isinstance(data, list):
            # Chunk list by items
            for i, item in enumerate(data):
                chunk_text = json.dumps(item, indent=2)
                
                # If chunk is too large, recursively chunk it
                if self._count_tokens(chunk_text) > self.max_chunk_size:
                    sub_chunks = self._chunk_json_recursive(item, [f'[{i}]'], metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': len(chunks),
                        'path': f'[{i}]',
                        'type': type(item).__name__,
                        'chunking_method': 'structure',
                    })
                    chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        else:
            # Primitive type, return as single chunk
            chunk_metadata = metadata.copy()
            chunk_metadata['chunking_method'] = 'structure'
            chunks.append(self._create_document(str(data), chunk_metadata))
        
        return chunks
    
    def _chunk_json_recursive(self, data: Any, path: List[str], metadata: Dict[str, Any]) -> List[Document]:
        """
        Recursively chunk large JSON objects.
        
        Args:
            data: JSON data to chunk
            path: Current path in the JSON structure
            metadata: Base metadata
            
        Returns:
            List of Document objects
        """
        chunks = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = path + [key]
                chunk_data = {key: value}
                chunk_text = json.dumps(chunk_data, indent=2)
                
                if self._count_tokens(chunk_text) > self.max_chunk_size:
                    sub_chunks = self._chunk_json_recursive(value, current_path, metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': len(chunks),
                        'path': '.'.join(current_path),
                        'type': type(value).__name__,
                        'chunking_method': 'structure',
                    })
                    chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = path + [f'[{i}]']
                chunk_text = json.dumps(item, indent=2)
                
                if self._count_tokens(chunk_text) > self.max_chunk_size:
                    sub_chunks = self._chunk_json_recursive(item, current_path, metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': len(chunks),
                        'path': '.'.join(current_path),
                        'type': type(item).__name__,
                        'chunking_method': 'structure',
                    })
                    chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        else:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'path': '.'.join(path),
                'chunking_method': 'structure',
            })
            chunks.append(self._create_document(str(data), chunk_metadata))
        
        return chunks
    
    def _chunk_xml(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        Chunk XML content.
        
        Args:
            content: XML string
            metadata: Metadata for chunks
            
        Returns:
            List of Document objects
        """
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            # If parsing fails, return as single chunk with error
            chunk_metadata = metadata.copy()
            chunk_metadata['parse_error'] = str(e)
            return [self._create_document(content, chunk_metadata)]
        
        chunks = []
        
        # Chunk by top-level elements
        for i, element in enumerate(root):
            chunk_text = ET.tostring(element, encoding='unicode')
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'tag': element.tag,
                'path': f'{root.tag}.{element.tag}[{i}]',
                'chunking_method': 'structure',
            })
            
            chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        # If no child elements, return root as single chunk
        if not chunks:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'tag': root.tag,
                'chunking_method': 'structure',
            })
            chunks.append(self._create_document(content, chunk_metadata))
        
        return chunks
