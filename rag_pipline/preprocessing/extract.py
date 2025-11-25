import pandas as pd
import threading
import os
import re
from typing import List
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.datamodel.base_models import InputFormat
from rag_pipline.utils.db_connection import ConnectionManager
from rag_pipline.utils.generator import TableDescriptionGenerator
from rag_pipline.config import TableDescriptionConfig

class Extractor:
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.table_desc_generator = TableDescriptionGenerator(TableDescriptionConfig())

    def _upload_table(self, user_id: str, df: pd.DataFrame, table_name: str):
        try:
            records = df.to_dict(orient='records')
            for record in records:
                self.connection_manager.get_postgres().push(user_id, table_name, record)
            print(f"Table {table_name} uploaded asynchronously.")
        except Exception as e:
            print(f"Error uploading table {table_name}: {e}")

    def _upload_image(self, user_id: str, org_id: str, image_path: str, image_name: str):
        try:
            self.connection_manager.get_minio().push(org_id, user_id, "images", image_path, image_name)
            print(f"Image {image_name} uploaded asynchronously.")
        except Exception as e:
            print(f"Error uploading image {image_name}: {e}")

    def _fix_table_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyzes and fixes incorrect table headers using heuristic detection.
        
        Algorithm:
        1. Check if header needs fixing using heuristics:
           - Count columns with "Unnamed" pattern
           - Count columns with generic patterns (col1, col2, etc.)
           - Check for duplicate column names
        2. If issues detected, search through rows to find valid header
        3. Promote the first row with unique column names
        """
        if df.empty or len(df) < 1:
            return df
            
        # Heuristic checks
        total_cols = len(df.columns)
        if total_cols == 0:
            return df
        
        # Check 1: Count unnamed columns
        unnamed_count = sum(1 for col in df.columns if 'unnamed' in str(col).lower())
        
        # Check 2: Count generic column names
        generic_count = sum(1 for col in df.columns if re.match(r'^(col|column)\d*$', str(col).lower()))
        
        # Check 3: Check for duplicate column names
        unique_cols = len(set(str(col).lower() for col in df.columns))
        has_duplicates = unique_cols < total_cols
        
        # Determine if header needs fixing
        needs_fixing = (
            (unnamed_count + generic_count) / total_cols > 0.5 or  # >50% generic/unnamed
            has_duplicates  # Has duplicate column names
        )
        
        if needs_fixing:
            # Search through rows to find valid header (check up to 5 rows)
            max_rows_to_check = min(5, len(df))
            
            for row_idx in range(max_rows_to_check):
                candidate_row = df.iloc[row_idx]
                
                # Check if this row has mostly strings (good header candidates)
                string_ratio = candidate_row.apply(lambda x: isinstance(x, str)).sum() / total_cols
                
                if string_ratio > 0.7:
                    # Check if all values are unique (no duplicates)
                    candidate_values = [str(val).strip() for val in candidate_row.values]
                    unique_values = len(set(candidate_values))
                    
                    if unique_values == total_cols:
                        # Found a valid header! Promote this row
                        df.columns = candidate_row.values
                        df = df.iloc[row_idx + 1:].reset_index(drop=True)
                        print(f"Header fixed: Promoted row {row_idx} to header")
                        break
        
        return df

    def _merge_tables(self, docling_tables: List) -> List[dict]:
        """
        Merges tables that span multiple pages.
        
        Algorithm:
        1. Sort tables by page number
        2. For each table, check if next table is continuation
        3. Merge if conditions are met
        
        Returns:
            List of dicts with 'df' and 'page' keys
        """
        if not docling_tables:
            return []
        
        # Convert to list with metadata
        tables_with_meta = []
        for table in docling_tables:
            df = table.export_to_dataframe()
            page_no = table.prov[0].page_no if table.prov else 1
            tables_with_meta.append({
                'df': df,
                'page': page_no,
                'table_obj': table
            })
        
        # Sort by page number
        tables_with_meta.sort(key=lambda x: x['page'])
        
        merged_tables = []
        skip_indices = set()
        
        for i in range(len(tables_with_meta)):
            if i in skip_indices:
                continue
                
            current = tables_with_meta[i]
            merged_df = current['df'].copy()
            
            # Try to merge with subsequent tables
            j = i + 1
            while j < len(tables_with_meta):
                next_table = tables_with_meta[j]
                
                # Check merge conditions
                is_consecutive_page = (next_table['page'] == current['page'] + (j - i))
                same_col_count = len(merged_df.columns) == len(next_table['df'].columns)
                
                if is_consecutive_page and same_col_count:
                    # Check if headers match (case-insensitive) or next table has generic header
                    next_df = next_table['df']
                    headers_match = all(
                        str(c1).lower() == str(c2).lower() 
                        for c1, c2 in zip(merged_df.columns, next_df.columns)
                    )
                    
                    next_has_generic = sum(
                        1 for col in next_df.columns 
                        if 'unnamed' in str(col).lower() or re.match(r'^(col|column)\d*$', str(col).lower())
                    ) / len(next_df.columns) > 0.5
                    
                    if headers_match or next_has_generic:
                        # Merge the tables
                        next_df.columns = merged_df.columns  # Align column names
                        merged_df = pd.concat([merged_df, next_df], ignore_index=True)
                        skip_indices.add(j)
                        j += 1
                    else:
                        break
                else:
                    break
            
            merged_tables.append({
                'df': merged_df,
                'page': current['page']
            })
        
        return merged_tables

    def extract(self, file_path: str, user_id: str, org_id: str, useOCR: bool = False) -> List[Document]:
        # Configure Pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = useOCR
        
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching=True
        )

        # Configure Converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Convert
        print(f"Converting {file_path}...")
        converted_doc = converter.convert(file_path)
        doc = converted_doc.document
        
        text_docs = []

        # Extract text
        for item in doc.texts:
            lc_doc = Document(
                page_content=item.text,
                metadata={
                    "source": file_path,
                    "content_type": "text",
                    "source_file_type": "pdf",
                    "page": item.prov[0].page_no if item.prov else 1
                }
            )
            text_docs.append(lc_doc)

        # STEP 1: Extract all tables from docling
        raw_tables = list(doc.tables)
        
        # STEP 2: Merge tables spanning multiple pages
        merged_tables = self._merge_tables(raw_tables)
        
        # STEP 3: Process each merged table
        for i, table_info in enumerate(merged_tables):
            df = table_info['df']
            page_no = table_info['page']
            
            # Fix header if needed
            df = self._fix_table_header(df)
            
            table_name = f"table_p{page_no}_t{i}"
            
            # Determine storage strategy based on size
            if df.shape[0] <= 10 and df.shape[1] <= 10:
                # Small table: Add as markdown with description
                markdown_table = df.to_markdown()
                
                # Generate description
                try:
                    description = self.table_desc_generator.generate_description({
                        "columns": list(df.columns),
                        "sample_rows": df.head(3).to_dict('records'),
                        "row_count": len(df),
                        "page": page_no
                    })
                    content = f"{description}\n\n{markdown_table}"
                except Exception as e:
                    print(f"Error generating description for table {table_name}: {e}")
                    content = markdown_table
                
                text_docs.append(Document(
                    page_content=content,
                    metadata={
                        "source": file_path,
                        "content_type": "table",
                        "source_file_type": "pdf",
                        "page": page_no,
                        "table_size": "small"
                    }
                ))
            else:
                # Large table: Upload to PostgreSQL with description
                t = threading.Thread(target=self._upload_table, args=(user_id, df, table_name))
                t.start()
                
                # Generate description for placeholder
                try:
                    description = self.table_desc_generator.generate_description({
                        "columns": list(df.columns),
                        "sample_rows": df.head(3).to_dict('records'),
                        "row_count": len(df),
                        "page": page_no
                    })
                    table_summary = f"{description}\n\nTable stored in database: {table_name}"
                except Exception as e:
                    print(f"Error generating description for table {table_name}: {e}")
                    table_summary = f"Table containing columns: {list(df.columns)}, Located on page: {page_no}"
                
                text_docs.append(Document(
                    page_content=table_summary,
                    metadata={
                        "source": file_path,
                        "content_type": "table",
                        "source_file_type": "pdf",
                        "page": page_no,
                        "table_name": table_name,
                        "table_size": "large"
                    }
                ))

        # Extract images
        for i, image in enumerate(doc.pictures):
            page_no = image.prov[0].page_no if image.prov else 1
            image_name = f"image_p{page_no}_{i}.png"
            temp_path = f"temp_{image_name}"
            
            # Save image
            image.image.save(temp_path)
            
            # Async Upload
            t = threading.Thread(target=self._upload_image, args=(user_id, org_id, temp_path, image_name))
            t.start()
            
            # Add image metadata
            text_docs.append(Document(
                page_content="",
                metadata={
                    "source": file_path,
                    "content_type": "image",
                    "source_file_type": "pdf",
                    "page": page_no,
                    "local_path": os.path.abspath(temp_path)
                }
            ))
            
        return text_docs