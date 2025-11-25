from PIL import Image
import torch
from transformers import AutoProcessor, AutModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
from typing import List

from rag_pipline.config import ImageDescriptionConfig, TableDescriptionConfig

class ImageDescriptionGenerator:
    def __init__(self, config: ImageDescriptionConfig):
        self.device = config.device
        self.batch_size = config.batch_size
        self.processor = AutoProcessor.from_pretrained(config.model_id, trust_remote_code=True)
        self.model = AutModelForCausalLM.from_pretrained(config.model_id, trust_remote_code=True).to(self.device)

    def generate(self, images: List[Image]) -> List[str]:
        ln = len(images)
        descriptions = []
        for i in range(0, ln, self.batch_size): 
            descriptions.extend(self.generate(images[i:i + self.batch_size]))
        return descriptions
    
    def generate_query(self, image: Image) -> str:
        return self.generate([image])[0]

class TableDescriptionGenerator:
    def __init__(self, config: TableDescriptionConfig):
        self.device = config.device
        self.batch_size = config.batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(config.model_id, trust_remote_code=True).to(self.device)

    def _generate_batch(self, prompts: List[str]) -> List[str]:
        """Generate descriptions for a batch of prompts."""
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=150,
                num_beams=4,
                early_stopping=True
            )
        
        descriptions = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return descriptions

    def generate_description(self, table_data: dict) -> str:
        """
        Generates semantic description of a table.
        
        Args:
            table_data: Dict with keys:
                - columns: List of column names
                - sample_rows: List of dicts (first few rows)
                - row_count: Total number of rows
                - page: Page number
        
        Returns:
            Semantic description of the table
        """
        columns = table_data.get('columns', [])
        sample_rows = table_data.get('sample_rows', [])
        row_count = table_data.get('row_count', 0)
        page = table_data.get('page', 'unknown')
        
        # Create prompt
        prompt = f"""Analyze this table and provide a concise description:
Columns: {', '.join(str(c) for c in columns)}
Sample data: {sample_rows[:3]}
Total rows: {row_count}
Page: {page}

Describe what information this table contains and its purpose."""
        
        descriptions = self._generate_batch([prompt])
        return descriptions[0]
    
    def generate_descriptions(self, tables_data: List[dict]) -> List[str]:
        """Generate descriptions for multiple tables in batches."""
        all_descriptions = []
        for i in range(0, len(tables_data), self.batch_size):
            batch = tables_data[i:i + self.batch_size]
            prompts = []
            
            for table_data in batch:
                columns = table_data.get('columns', [])
                sample_rows = table_data.get('sample_rows', [])
                row_count = table_data.get('row_count', 0)
                page = table_data.get('page', 'unknown')
                
                prompt = f"""Analyze this table and provide a concise description:
Columns: {', '.join(str(c) for c in columns)}
Sample data: {sample_rows[:3]}
Total rows: {row_count}
Page: {page}

Describe what information this table contains and its purpose."""
                prompts.append(prompt)
            
            batch_descriptions = self._generate_batch(prompts)
            all_descriptions.extend(batch_descriptions)
        
        return all_descriptions