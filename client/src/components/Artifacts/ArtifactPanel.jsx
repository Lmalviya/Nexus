import React, { useState } from 'react';
import { FileText, Trash2, Upload, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import axios from 'axios';
import { useUpload } from '../../context/UploadContext';

const ArtifactPanel = ({ sessionId }) => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const { uploads } = useUpload();

    const fetchDocuments = async () => {
        try {
            const response = await axios.get('http://localhost:8000/files');
            setDocuments(response.data);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
        }
    };

    // Fetch documents on mount and when uploads change
    React.useEffect(() => {
        fetchDocuments();
    }, [uploads]); // Re-fetch when uploads change (e.g. new upload success)

    const handleDelete = async (fileKey, filename) => {
        if (!confirm(`Delete "${filename}"?`)) return;

        setLoading(true);
        try {
            await axios.delete(`http://localhost:8000/files/${fileKey}?session_id=${sessionId}`);
            setDocuments(prev => prev.filter(doc => doc.file_key !== fileKey));
            alert('Document deleted successfully');
        } catch (error) {
            console.error('Delete failed:', error);
            alert('Failed to delete document');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="text-sm font-semibold uppercase tracking-wider">Documents</h2>
                <div className="flex gap-2">
                    <span className="text-xs text-muted-foreground">{documents.length} files</span>
                </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
                {/* Upload Progress Section */}
                {uploads.length > 0 && (
                    <div className="space-y-2 mb-4">
                        {uploads.map((upload) => (
                            <div
                                key={upload.id}
                                className="flex items-center justify-between p-3 border border-border rounded-lg bg-accent/30"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    {upload.status === 'uploading' && (
                                        <Loader2 size={20} className="text-primary flex-shrink-0 animate-spin" />
                                    )}
                                    {upload.status === 'success' && (
                                        <CheckCircle2 size={20} className="text-green-500 flex-shrink-0" />
                                    )}
                                    {upload.status === 'error' && (
                                        <XCircle size={20} className="text-red-500 flex-shrink-0" />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{upload.filename}</p>
                                        {upload.status === 'uploading' && (
                                            <div className="mt-1">
                                                <div className="w-full bg-secondary rounded-full h-1.5">
                                                    <div
                                                        className="bg-primary h-1.5 rounded-full transition-all duration-300"
                                                        style={{ width: `${upload.progress}%` }}
                                                    ></div>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {upload.progress}%
                                                </p>
                                            </div>
                                        )}
                                        {upload.status === 'success' && (
                                            <p className="text-xs text-green-500">Upload complete!</p>
                                        )}
                                        {upload.status === 'error' && (
                                            <p className="text-xs text-red-500">{upload.error || 'Upload failed'}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Documents List */}
                {documents.length === 0 && uploads.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
                        <div className="p-4 rounded-full bg-secondary/50">
                            <FileText size={32} />
                        </div>
                        <p className="text-sm">No documents uploaded yet</p>
                        <p className="text-xs">Use the paperclip button to upload files</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {documents.map((doc) => (
                            <div
                                key={doc.file_key}
                                className="flex items-center justify-between p-3 border border-border rounded-lg hover:bg-accent/50 transition-colors"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <FileText size={20} className="text-primary flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{doc.filename}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {(doc.file_size / 1024).toFixed(1)} KB
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(doc.file_key, doc.filename)}
                                    disabled={loading}
                                    className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded transition-colors disabled:opacity-50"
                                    title="Delete document"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ArtifactPanel;
