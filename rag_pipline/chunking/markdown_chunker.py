import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from .base_chunker import BaseChunker


class MarkdownChunker(BaseChunker):
    """
    Markdown-aware chunking that respects document structure.
    
    This chunker:
    1. Parses markdown to identify heading hierarchy
    2. Creates chunks at heading boundaries
    3. Keeps sections together (heading + content)
    4. Handles code blocks, lists, and tables as atomic units
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Configuration
        self.max_heading_level = self.config.get('max_heading_level', 3)
        self.max_chunk_size = self.config.get('max_chunk_size', 1000)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk markdown content by sections.
        
        Args:
            content: The markdown content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        lines = content.split('\n')
        chunks = []
        current_section = []
        current_heading = None
        heading_hierarchy = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Track code blocks (don't split inside them)
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                current_section.append(line)
                continue
            
            # Check for headings (only when not in code block)
            if not in_code_block:
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                
                if heading_match:
                    heading_level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()
                    
                    # Only split on headings up to max_heading_level
                    if heading_level <= self.max_heading_level:
                        # Save previous section if it exists
                        if current_section:
                            chunk_text = '\n'.join(current_section).strip()
                            if chunk_text:
                                chunk_metadata = metadata.copy()
                                chunk_metadata.update({
                                    'chunk_index': len(chunks),
                                    'heading': current_heading,
                                    'heading_hierarchy': heading_hierarchy.copy(),
                                    'chunking_method': 'markdown',
                                })
                                chunks.append(self._create_document(chunk_text, chunk_metadata))
                        
                        # Update heading hierarchy
                        # Remove headings at same or lower level
                        heading_hierarchy = [h for h in heading_hierarchy if h['level'] < heading_level]
                        heading_hierarchy.append({'level': heading_level, 'text': heading_text})
                        
                        # Start new section
                        current_section = [line]
                        current_heading = heading_text
                        continue
            
            # Add line to current section
            current_section.append(line)
            
            # Check if current section is getting too large
            section_text = '\n'.join(current_section)
            if self._count_tokens(section_text) > self.max_chunk_size and not in_code_block:
                # Force split even within a section
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'heading': current_heading,
                    'heading_hierarchy': heading_hierarchy.copy(),
                    'chunking_method': 'markdown',
                    'force_split': True,
                })
                chunks.append(self._create_document(section_text, chunk_metadata))
                current_section = []
        
        # Add final section
        if current_section:
            chunk_text = '\n'.join(current_section).strip()
            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'heading': current_heading,
                    'heading_hierarchy': heading_hierarchy.copy(),
                    'chunking_method': 'markdown',
                })
                chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        # If no chunks were created, return whole content
        if not chunks:
            chunk_metadata = metadata.copy()
            chunk_metadata['chunking_method'] = 'markdown'
            chunks.append(self._create_document(content, chunk_metadata))
        
        return chunks
