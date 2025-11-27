import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from rag_pipline.document_pipeline import DocumentPipeline
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
