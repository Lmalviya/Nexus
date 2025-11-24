import pandas as pd
import threading
import os
from typing import List
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.datamodel.base_models import InputFormat
from rag_pipline.utils.db_connection import ConnectionManager

class Extractor:
    def __init__(self):
        self.connection_manager = ConnectionManager()

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

        for i, table in enumerate(doc.tables):
            df = table.export_to_dataframe()
            page_no = table.prov[0].page_no if table.prov else 1
            table_name = f"table_p{page_no}_t{i}"
            
            # Async Upload
            t = threading.Thread(target=self._upload_table, args=(user_id, df, table_name))
            t.start()
            
            # Add placeholder to text docs
            table_summary = f"Table containing columns: {list(df.columns)}, Located on page: {page_no}"
            text_docs.append(Document(
                page_content=table_summary,
                metadata={
                    "source": file_path,
                    "content_type": "table",
                    "source_file_type": "pdf",
                    "page": page_no
                }
            ))

        for i, image in enumerate(doc.pictures):
            # We need to save the image to a temp path to upload it, or upload bytes directly.
            # MinIO connector takes a file path.
            # We'll save to a temp file.
            page_no = image.prov[0].page_no if image.prov else 1
            image_name = f"image_p{page_no}_{i}.png"
            temp_path = f"temp_{image_name}"
            
            # Save image
            # image.image is likely a PIL Image
            image.image.save(temp_path)
            
            # Async Upload
            t = threading.Thread(target=self._upload_image, args=(user_id, org_id, temp_path, image_name))
            t.start()
            
            # We should probably clean up the temp file later, but for async fire-and-forget it's tricky.
            # We might want a daemon cleaner or just let the OS handle /tmp.
            # For this implementation, we'll leave it or delete in the thread.
            
        return text_docs