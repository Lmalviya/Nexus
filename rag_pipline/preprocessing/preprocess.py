import pypdf



class PDFHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def isPasswordProtected(self):
        try:
            reader = pypdf.PdfReader(self.file_path)
            return reader.isEncrypted
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return True 

    def pdf_handler(self, file_path):
        try:
            reader = pypdf.PdfReader(file_path)
            isTrue = self.isPasswordProtected(reader)
            if isTrue: 
                return [], "file is corrupted or password protected"
            
            
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None



class FilePreprocessor:
    def __init__(self):
        hasher = hashlib.md5()

    def check_file_hash_in_db(self, file_hash):
        pass

    def computeHash(self, file_path: str):
        with open(file_path, 'rb') as f:
            self.hasher.update(f.read())
        return self.hasher.hexdigest()

    def is_file_available(self, file_path):
        file_hash = self.computeHash(file_path)
        return self.check_file_hash_in_db(file_hash)
        
    def file_extention(self, file_path):
        return file_path.split('.')[-1]
    
    
    def docx_handler(self, file_path):
        pas
    def txt_handler(self, file_path):
        pass
    def image_handler(self, file_path):
        pass
    def csv_handler(self, file_path):
        pass
    def json_handler(self, file_path):
        pass
    def xml_handler(self, file_path):
        pass

    def preprocess(self, file_path):
        file_type = self.file_extention(file_path)

        if file_type == 'pdf':
            pass
        elif file_type == 'docx':
            pass
        elif file_type == 'txt':
            pass
        elif file_type == "png" or file_type == "jpg" or file_type == "jpeg":
            pass
        elif file_type == 'csv':
            pass
        elif file_type == 'json':
            pass
        elif file_type == 'xml':
            pass
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        