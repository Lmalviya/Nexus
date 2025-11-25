import pandas as pd
import threading
from typing import List, Tuple
from langchain_core.documents import Document
from rag_pipline.utils.db_connection import ConnectionManager
from rag_pipline.utils.generator import TableDescriptionGenerator
from rag_pipline.config import TableDescriptionConfig


class SpreadsheetHandler:
    """Handler for CSV, Excel, and other spreadsheet formats."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.table_desc_generator = TableDescriptionGenerator(TableDescriptionConfig())
    
    def _upload_table(self, user_id: str, df: pd.DataFrame, table_name: str):
        """Upload table data to PostgreSQL."""
        try:
            records = df.to_dict(orient='records')
            for record in records:
                self.connection_manager.get_postgres().push(user_id, table_name, record)
            print(f"Table {table_name} uploaded asynchronously.")
        except Exception as e:
            print(f"Error uploading table {table_name}: {e}")
    
    def _read_file(self, file_path: str) -> pd.DataFrame:
        """
        Read spreadsheet file into DataFrame.
        Supports: CSV, Excel (.xlsx, .xls), Google Sheets export, etc.
        """
        file_ext = file_path.lower().split('.')[-1]
        
        try:
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['xlsx', 'xls', 'xlsm', 'xlsb']:
                # Read first sheet by default
                df = pd.read_excel(file_path, sheet_name=0)
            elif file_ext == 'ods':  # OpenDocument Spreadsheet
                df = pd.read_excel(file_path, engine='odf')
            elif file_ext == 'tsv':  # Tab-separated values
                df = pd.read_csv(file_path, sep='\t')
            else:
                raise ValueError(f"Unsupported spreadsheet format: {file_ext}")
            
            return df
        except Exception as e:
            raise Exception(f"Error reading spreadsheet file: {str(e)}")
    
    def process_spreadsheet(self, file_path: str, user_id: str, org_id: str) -> Tuple[List[Document], str]:
        """
        Process spreadsheet file and return LangChain documents.
        
        Args:
            file_path: Path to spreadsheet file
            user_id: User ID for database storage
            org_id: Organization ID
        
        Returns:
            Tuple[List[Document], str]: (documents, error_message)
        """
        try:
            # Read spreadsheet
            df = self._read_file(file_path)
            
            if df.empty:
                return [], "Spreadsheet is empty"
            
            # Generate table name
            file_name = file_path.split('/')[-1].split('\\')[-1].split('.')[0]
            table_name = f"spreadsheet_{file_name}_{user_id}"
            
            # Upload to PostgreSQL asynchronously
            t = threading.Thread(target=self._upload_table, args=(user_id, df, table_name))
            t.start()
            
            # Generate description
            try:
                description = self.table_desc_generator.generate_description({
                    "columns": list(df.columns),
                    "sample_rows": df.head(3).to_dict('records'),
                    "row_count": len(df),
                    "page": "N/A"
                })
                content = f"{description}\n\nTable stored in database: {table_name}"
            except Exception as e:
                print(f"Error generating description: {e}")
                content = f"Spreadsheet with columns: {list(df.columns)}\nRows: {len(df)}\nTable: {table_name}"
            
            # Create LangChain document
            doc = Document(
                page_content=content,
                metadata={
                    "source": file_path,
                    "content_type": "spreadsheet",
                    "source_file_type": file_path.split('.')[-1],
                    "table_name": table_name,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns)
                }
            )
            
            return [doc], ""
            
        except Exception as e:
            error_msg = f"Error processing spreadsheet: {str(e)}"
            print(error_msg)
            return [], error_msg
