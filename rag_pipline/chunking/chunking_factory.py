import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from .base_chunker import BaseChunker
from .code_chunker import CodeChunker
from .semantic_chunker import SemanticChunker
from .sentence_chunker import SentenceChunker
from .markdown_chunker import MarkdownChunker
from .fixed_chunker import FixedChunker
from .structure_chunker import StructureChunker


class ChunkingFactory:
    """
    Factory class that routes files to appropriate chunkers based on file type.
    
    Automatically selects the optimal chunking strategy for different file types:
    - Code files: Function/class-based chunking
    - Markdown: Structure-aware chunking
    - JSON/XML: Structure-aware chunking
    - Text: Semantic or sentence-based chunking
    - Unknown: Fixed-size chunking (fallback)
    """
    
    # File type mappings
    FILE_TYPE_MAPPINGS = {
        'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.ts', '.tsx', 
                 '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.cs'],
        'markdown': ['.md', '.rst', '.mdx'],
        'structured': ['.json', '.xml', '.yaml', '.yml'],
        'html': ['.html', '.htm'],
        'text': ['.txt', '.log', '.csv', '.tsv'],
    }
    
    # Language detection for code files
    EXTENSION_TO_LANGUAGE = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'cpp',
        '.h': 'cpp',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.cs': 'csharp',
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the chunking factory.
        
        Args:
            config: Configuration dictionary for chunkers
        """
        self.config = config or {}
        
        # Initialize chunkers (lazy initialization)
        self._chunkers = {}
    
    def get_file_type(self, file_path: str) -> str:
        """
        Determine file type category from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type category: 'code', 'markdown', 'structured', 'html', 'text', or 'unknown'
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        for file_type, extensions in self.FILE_TYPE_MAPPINGS.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    def get_language(self, file_path: str) -> Optional[str]:
        """
        Get programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name or None
        """
        ext = os.path.splitext(file_path)[1].lower()
        return self.EXTENSION_TO_LANGUAGE.get(ext)
    
    def get_chunker(self, file_type: str) -> BaseChunker:
        """
        Get or create a chunker for the given file type.
        
        Args:
            file_type: File type category
            
        Returns:
            Appropriate chunker instance
        """
        # Return cached chunker if available
        if file_type in self._chunkers:
            return self._chunkers[file_type]
        
        # Create new chunker based on file type
        if file_type == 'code':
            chunker = CodeChunker(self.config.get('code', {}))
        elif file_type == 'markdown':
            chunker = MarkdownChunker(self.config.get('markdown', {}))
        elif file_type == 'structured':
            chunker = StructureChunker(self.config.get('structure', {}))
        elif file_type == 'text':
            # Use semantic chunking for text by default, or sentence-based if configured
            default_text_chunker = self.config.get('default_text_chunker', 'semantic')
            if default_text_chunker == 'semantic':
                chunker = SemanticChunker(self.config.get('semantic', {}))
            else:
                chunker = SentenceChunker(self.config.get('sentence', {}))
        else:
            # Fallback to fixed chunking for unknown types
            chunker = FixedChunker(self.config.get('fixed', {}))
        
        # Cache the chunker
        self._chunkers[file_type] = chunker
        return chunker
    
    def chunk_file(self, file_path: str, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk a file using the appropriate chunker.
        
        Args:
            file_path: Path to the file (used for type detection)
            content: File content to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        # Determine file type
        file_type = self.get_file_type(file_path)
        
        # Add file information to metadata
        metadata.update({
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': file_type,
        })
        
        # Add language for code files
        if file_type == 'code':
            language = self.get_language(file_path)
            if language:
                metadata['language'] = language
        
        # Add file type for structured files
        if file_type == 'structured':
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.json':
                metadata['file_type'] = 'json'
            elif ext in ['.xml']:
                metadata['file_type'] = 'xml'
            elif ext in ['.yaml', '.yml']:
                metadata['file_type'] = 'yaml'
        
        # Get appropriate chunker
        chunker = self.get_chunker(file_type)
        
        # Chunk the content
        chunks = chunker.chunk(content, metadata)
        
        return chunks
    
    def chunk_text(self, text: str, chunker_type: str = 'semantic', metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk raw text using a specific chunker type.
        
        Args:
            text: Text content to chunk
            chunker_type: Type of chunker to use ('semantic', 'sentence', 'fixed')
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        # Get appropriate chunker
        if chunker_type == 'semantic':
            chunker = self.get_chunker('text')  # Will use semantic by default
        elif chunker_type == 'sentence':
            if 'sentence' not in self._chunkers:
                self._chunkers['sentence'] = SentenceChunker(self.config.get('sentence', {}))
            chunker = self._chunkers['sentence']
        elif chunker_type == 'fixed':
            chunker = self.get_chunker('unknown')  # Will use fixed
        else:
            raise ValueError(f"Unknown chunker type: {chunker_type}")
        
        # Chunk the text
        chunks = chunker.chunk(text, metadata)
        
        return chunks
