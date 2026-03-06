"""
Example usage of the chunking module.

This file demonstrates how to use different chunking strategies
for various file types in the RAG pipeline.
"""

from rag_pipline.chunking import ChunkingFactory
from rag_pipline.config import ChunkingConfig


def example_chunk_python_code():
    """Example: Chunk Python code into functions and classes."""
    print("=" * 60)
    print("Example 1: Chunking Python Code")
    print("=" * 60)
    
    python_code = '''
import os
import sys

def hello_world():
    """Print hello world."""
    print("Hello, World!")

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def subtract(self, x):
        self.result -= x
        return self.result
'''
    
    # Create factory
    factory = ChunkingFactory()
    
    # Chunk the code
    chunks = factory.chunk_file('example.py', python_code)
    
    print(f"\nGenerated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Type: {chunk.metadata.get('type', 'N/A')}")
        print(f"  Name: {chunk.metadata.get('name', 'N/A')}")
        print(f"  Lines: {chunk.metadata.get('start_line', 'N/A')}-{chunk.metadata.get('end_line', 'N/A')}")
        print(f"  Content preview: {chunk.page_content[:100]}...")
        print()


def example_chunk_markdown():
    """Example: Chunk Markdown document by sections."""
    print("=" * 60)
    print("Example 2: Chunking Markdown")
    print("=" * 60)
    
    markdown_content = '''
# Introduction

This is the introduction section of the document.

## Background

Some background information here.

### History

Historical context goes here.

## Methodology

This section describes the methodology.

```python
def example():
    print("Code block")
```

## Results

The results are presented here.
'''
    
    factory = ChunkingFactory()
    chunks = factory.chunk_file('example.md', markdown_content)
    
    print(f"\nGenerated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Heading: {chunk.metadata.get('heading', 'N/A')}")
        print(f"  Hierarchy: {chunk.metadata.get('heading_hierarchy', [])}")
        print(f"  Content preview: {chunk.page_content[:80]}...")
        print()


def example_chunk_text_semantic():
    """Example: Chunk text using semantic similarity."""
    print("=" * 60)
    print("Example 3: Semantic Chunking")
    print("=" * 60)
    
    text_content = '''
Machine learning is a subset of artificial intelligence. It focuses on building systems that can learn from data. 
These systems improve their performance over time without being explicitly programmed.

Deep learning is a type of machine learning. It uses neural networks with multiple layers. 
These networks can learn complex patterns in large amounts of data.

Natural language processing is another important area. It deals with the interaction between computers and human language.
NLP enables computers to understand, interpret, and generate human language.

Computer vision allows machines to interpret visual information. It uses deep learning techniques to analyze images and videos.
Applications include facial recognition, object detection, and autonomous vehicles.
'''
    
    # Configure semantic chunking
    config = {
        'semantic': {
            'similarity_threshold': ChunkingConfig.semantic_similarity_threshold,
            'min_chunk_size': ChunkingConfig.semantic_min_chunk_size,
            'max_chunk_size': ChunkingConfig.semantic_max_chunk_size,
        }
    }
    
    factory = ChunkingFactory(config)
    chunks = factory.chunk_text(text_content, chunker_type='semantic')
    
    print(f"\nGenerated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Sentences: {chunk.metadata.get('num_sentences', 'N/A')}")
        print(f"  Content: {chunk.page_content}")
        print()


def example_chunk_json():
    """Example: Chunk JSON structure."""
    print("=" * 60)
    print("Example 4: Chunking JSON")
    print("=" * 60)
    
    json_content = '''
{
    "users": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "country": "USA"
            }
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "address": {
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "country": "USA"
            }
        }
    ],
    "metadata": {
        "version": "1.0",
        "created": "2024-01-01"
    }
}
'''
    
    factory = ChunkingFactory()
    chunks = factory.chunk_file('example.json', json_content)
    
    print(f"\nGenerated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Path: {chunk.metadata.get('path', 'N/A')}")
        print(f"  Type: {chunk.metadata.get('type', 'N/A')}")
        print(f"  Content preview: {chunk.page_content[:100]}...")
        print()


def example_chunk_with_custom_config():
    """Example: Use custom configuration."""
    print("=" * 60)
    print("Example 5: Custom Configuration")
    print("=" * 60)
    
    # Custom configuration
    custom_config = {
        'code': {
            'include_imports': True,
            'min_function_lines': 5,  # Only chunk functions with 5+ lines
        },
        'semantic': {
            'similarity_threshold': 0.8,  # Higher threshold = more strict
            'max_chunk_size': 256,  # Smaller chunks
        },
        'sentence': {
            'chunk_size': 256,
            'overlap_sentences': 3,
        }
    }
    
    factory = ChunkingFactory(custom_config)
    
    text = "This is a test. It has multiple sentences. Each sentence is short. But together they form a paragraph."
    chunks = factory.chunk_text(text, chunker_type='sentence')
    
    print(f"\nGenerated {len(chunks)} chunks with custom config\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk.page_content}")
        print()


if __name__ == "__main__":
    # Run all examples
    example_chunk_python_code()
    example_chunk_markdown()
    example_chunk_text_semantic()
    example_chunk_json()
    example_chunk_with_custom_config()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
