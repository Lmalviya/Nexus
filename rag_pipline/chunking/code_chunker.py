import ast
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from .base_chunker import BaseChunker


class CodeChunker(BaseChunker):
    """
    Function and class-based chunking for programming languages.
    
    Uses AST parsing for Python and regex-based parsing for other languages.
    Extracts functions, classes, and methods as separate chunks.
    """
    
    # Language-specific patterns for function/class detection
    LANGUAGE_PATTERNS = {
        'python': {
            'function': r'^(?:async\s+)?def\s+(\w+)\s*\(',
            'class': r'^class\s+(\w+)(?:\(.*?\))?:',
        },
        'javascript': {
            'function': r'(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*:\s*(?:async\s+)?function\s*\(',
            'class': r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{',
        },
        'typescript': {
            'function': r'(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*:\s*(?:async\s+)?function\s*\(',
            'class': r'class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
        },
        'java': {
            'function': r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{',
            'class': r'(?:public|private|protected|abstract|final|\s)+class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
        },
        'cpp': {
            'function': r'(?:[\w:]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const)?\s*\{',
            'class': r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+\w+)?\s*\{',
        },
        'go': {
            'function': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(',
            'class': r'type\s+(\w+)\s+struct\s*\{',
        },
        'rust': {
            'function': r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(',
            'class': r'(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?\s*\{',
        },
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.include_imports = self.config.get('include_imports', True)
        self.min_function_lines = self.config.get('min_function_lines', 3)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk code into functions and classes.
        
        Args:
            content: The code content to chunk
            metadata: Optional metadata (should include 'language' key)
            
        Returns:
            List of Document objects, each representing a code chunk
        """
        if metadata is None:
            metadata = {}
        
        language = metadata.get('language', 'python').lower()
        
        # Use AST for Python, regex for others
        if language == 'python':
            return self._chunk_python_ast(content, metadata)
        else:
            return self._chunk_regex(content, metadata, language)
    
    def _chunk_python_ast(self, content: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        Chunk Python code using AST parsing.
        
        Args:
            content: Python code content
            metadata: Metadata for chunks
            
        Returns:
            List of Document objects
        """
        chunks = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            # Extract imports if configured
            imports = []
            if self.include_imports:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_line = ast.get_source_segment(content, node)
                        if import_line:
                            imports.append(import_line)
            
            imports_text = '\n'.join(imports) if imports else ""
            
            # Extract functions and classes
            for node in ast.iter_child_nodes(tree):
                chunk_text = None
                chunk_metadata = metadata.copy()
                
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Extract function
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    # Skip very small functions if configured
                    if end_line - start_line < self.min_function_lines:
                        continue
                    
                    chunk_text = '\n'.join(lines[start_line:end_line])
                    chunk_metadata.update({
                        'type': 'function',
                        'name': node.name,
                        'start_line': start_line + 1,
                        'end_line': end_line,
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                    })
                    
                    # Add imports context
                    if imports_text:
                        chunk_text = imports_text + '\n\n' + chunk_text
                
                elif isinstance(node, ast.ClassDef):
                    # Extract class
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    chunk_text = '\n'.join(lines[start_line:end_line])
                    chunk_metadata.update({
                        'type': 'class',
                        'name': node.name,
                        'start_line': start_line + 1,
                        'end_line': end_line,
                        'methods': [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    })
                    
                    # Add imports context
                    if imports_text:
                        chunk_text = imports_text + '\n\n' + chunk_text
                
                if chunk_text:
                    chunks.append(self._create_document(chunk_text, chunk_metadata))
            
            # If no chunks were created, return the whole file as one chunk
            if not chunks:
                chunk_metadata = metadata.copy()
                chunk_metadata['type'] = 'module'
                chunks.append(self._create_document(content, chunk_metadata))
        
        except SyntaxError as e:
            # If parsing fails, return whole content as one chunk
            chunk_metadata = metadata.copy()
            chunk_metadata['type'] = 'module'
            chunk_metadata['parse_error'] = str(e)
            chunks.append(self._create_document(content, chunk_metadata))
        
        return chunks
    
    def _chunk_regex(self, content: str, metadata: Dict[str, Any], language: str) -> List[Document]:
        """
        Chunk code using regex patterns for non-Python languages.
        
        Args:
            content: Code content
            metadata: Metadata for chunks
            language: Programming language
            
        Returns:
            List of Document objects
        """
        chunks = []
        lines = content.split('\n')
        
        # Get patterns for the language
        patterns = self.LANGUAGE_PATTERNS.get(language, self.LANGUAGE_PATTERNS['javascript'])
        
        # Find all function and class definitions
        function_pattern = re.compile(patterns['function'], re.MULTILINE)
        class_pattern = re.compile(patterns['class'], re.MULTILINE)
        
        # Track positions of functions and classes
        positions = []
        
        for i, line in enumerate(lines):
            if function_pattern.search(line):
                match = function_pattern.search(line)
                name = next((g for g in match.groups() if g), 'anonymous')
                positions.append({'line': i, 'type': 'function', 'name': name})
            elif class_pattern.search(line):
                match = class_pattern.search(line)
                name = next((g for g in match.groups() if g), 'anonymous')
                positions.append({'line': i, 'type': 'class', 'name': name})
        
        # Extract chunks based on positions
        for idx, pos in enumerate(positions):
            start_line = pos['line']
            
            # Find end of this block (next definition or end of file)
            if idx + 1 < len(positions):
                end_line = positions[idx + 1]['line']
            else:
                end_line = len(lines)
            
            # Extract the block
            chunk_text = '\n'.join(lines[start_line:end_line])
            
            # Skip very small blocks
            if end_line - start_line < self.min_function_lines:
                continue
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'type': pos['type'],
                'name': pos['name'],
                'start_line': start_line + 1,
                'end_line': end_line,
            })
            
            chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        # If no chunks were created, return the whole file
        if not chunks:
            chunk_metadata = metadata.copy()
            chunk_metadata['type'] = 'module'
            chunks.append(self._create_document(content, chunk_metadata))
        
        return chunks
