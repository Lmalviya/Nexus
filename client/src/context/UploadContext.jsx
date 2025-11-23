import React, { createContext, useState, useContext } from 'react';

const UploadContext = createContext();

export const useUpload = () => useContext(UploadContext);

export const UploadProvider = ({ children }) => {
    const [uploads, setUploads] = useState([]);

    const addUpload = (file) => {
        const uploadId = Date.now() + Math.random();
        setUploads(prev => [...prev, {
            id: uploadId,
            filename: file.name,
            size: file.size,
            status: 'uploading', // 'uploading', 'success', 'error'
            progress: 0,
            error: null
        }]);
        return uploadId;
    };

    const updateUploadProgress = (uploadId, progress) => {
        setUploads(prev => prev.map(upload =>
            upload.id === uploadId
                ? { ...upload, progress }
                : upload
        ));
    };

    const setUploadSuccess = (uploadId) => {
        setUploads(prev => prev.map(upload =>
            upload.id === uploadId
                ? { ...upload, status: 'success', progress: 100 }
                : upload
        ));

        // Remove from list after 3 seconds
        setTimeout(() => {
            setUploads(prev => prev.filter(upload => upload.id !== uploadId));
        }, 3000);
    };

    const setUploadError = (uploadId, error) => {
        setUploads(prev => prev.map(upload =>
            upload.id === uploadId
                ? { ...upload, status: 'error', error }
                : upload
        ));

        // Remove from list after 5 seconds
        setTimeout(() => {
            setUploads(prev => prev.filter(upload => upload.id !== uploadId));
        }, 5000);
    };

    return (
        <UploadContext.Provider value={{
            uploads,
            addUpload,
            updateUploadProgress,
            setUploadSuccess,
            setUploadError
        }}>
            {children}
        </UploadContext.Provider>
    );
};
