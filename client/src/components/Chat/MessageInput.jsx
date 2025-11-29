import React, { useState, useRef } from 'react';
import { Send, Paperclip, Mic, X } from 'lucide-react';
import axios from 'axios';
import { useConversation } from '../../context/ConversationContext';
import { useUpload } from '../../context/UploadContext';
import ModelSelector from './ModelSelector';

const MessageInput = ({ onSendMessage }) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef(null);
    const fileInputRef = useRef(null);
    const { addUpload, updateUploadProgress, setUploadSuccess, setUploadError } = useUpload();
    const { currentSessionId } = useConversation();

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        onSendMessage(input);
        setInput('');
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleChange = (e) => {
        setInput(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const uploadId = addUpload(file);

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (currentSessionId) {
                formData.append('session_id', currentSessionId);
            }

            const response = await axios.post('http://localhost:8000/files/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    // Authorization header is handled by interceptor or context usually
                    // If not, add it here: 'Authorization': `Bearer ${token}`
                },
                onUploadProgress: (progressEvent) => {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    updateUploadProgress(uploadId, progress);
                }
            });

            setUploadSuccess(uploadId);
            console.log('Upload success:', response.data);

            // Optionally add a system message or notification about the upload

        } catch (error) {
            console.error('File upload failed:', error);
            setUploadError(uploadId, error.message || 'Upload failed');
        } finally {
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="space-y-2">
            <div className="flex justify-between items-center px-1">
                <ModelSelector />
            </div>

            <form onSubmit={handleSubmit} className="relative flex items-end gap-2 p-2 border border-gray-700 rounded-xl bg-gray-800/50 shadow-sm focus-within:ring-1 focus-within:ring-blue-500/50">
                <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileUpload}
                    className="hidden"
                    accept="*/*"
                />
                <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
                    title="Attach file"
                >
                    <Paperclip size={20} />
                </button>

                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Message Nexus..."
                    className="flex-1 max-h-[200px] py-2 bg-transparent border-none focus:ring-0 resize-none placeholder:text-gray-500 text-gray-200 scrollbar-hide"
                    rows={1}
                />

                <div className="flex gap-1">
                    <button
                        type="button"
                        className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        type="submit"
                        disabled={!input.trim()}
                        className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </form>
        </div>
    );
};

export default MessageInput;
