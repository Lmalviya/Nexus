-- Add processing_status to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';

-- Create index for status filtering
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);

-- Add check constraint for valid statuses
ALTER TABLE documents 
ADD CONSTRAINT check_processing_status 
CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));
