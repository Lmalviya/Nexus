import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { cn } from '../../utils/cn';
import { useConversation } from '../../context/ConversationContext';
import { useUpload } from '../../context/UploadContext';
const MessageInput = ({ onSendMessage }) => {
    const [input, setInput] = useState('');
    const [selectedModel, setSelectedModel] = useState(null);
    const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
    const [availableProviders, setAvailableProviders] = useState([]);
    const textareaRef = useRef(null);
    const fileInputRef = useRef(null);
    const { addUpload, updateUploadProgress, setUploadSuccess, setUploadError } = useUpload();

    // Model configurations
    const modelConfigs = {
        openai: {
            name: 'OpenAI',
            models: [
                { id: 'gpt-4', name: 'GPT-4' },
                { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
                { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' }
            ]
        },
        claude: {
            name: 'Claude',
            models: [
                { id: 'claude-3-opus', name: 'Claude 3 Opus' },
                { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet' },
                { id: 'claude-3-haiku', name: 'Claude 3 Haiku' }
            ]
        },
        gemini: {
            name: 'Gemini',
            models: [
                { id: 'gemini-pro', name: 'Gemini Pro' },
                { id: 'gemini-pro-vision', name: 'Gemini Pro Vision' }
            ]
        },
        cohere: {
            name: 'Cohere',
            models: [
                { id: 'command', name: 'Command' },
                { id: 'command-light', name: 'Command Light' }
            ]
        },
        huggingface: {
            name: 'HuggingFace',
            models: [
                { id: 'mistral-7b', name: 'Mistral 7B' },
                { id: 'llama-2-70b', name: 'Llama 2 70B' }
            ]
        },
        mistral: {
            name: 'Mistral AI',
            models: [
                { id: 'mistral-large', name: 'Mistral Large' },
                { id: 'mistral-medium', name: 'Mistral Medium' }
            ]
        }
    };

    // Check which providers have API keys from backend
    useEffect(() => {
        const checkApiKeys = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api-keys');
                const keys = response.data.keys || [];
                // Get unique providers from the keys array
                const providers = [...new Set(keys.map(k => k.provider))];

                setAvailableProviders(providers);

                // Set default model if none selected
                if (!selectedModel && providers.length > 0) {
                    const firstProvider = providers[0];
                    if (modelConfigs[firstProvider]) {
                        setSelectedModel({
                            provider: firstProvider,
                            model: modelConfigs[firstProvider].models[0]
                        });
                    }
                }
            } catch (error) {
                console.error('Failed to fetch API keys:', error);
                setAvailableProviders([]);
            }
        };

        checkApiKeys();
        // Re-check when window gains focus (in case settings were changed)
        window.addEventListener('focus', checkApiKeys);
        return () => window.removeEventListener('focus', checkApiKeys);
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        onSendMessage(input, selectedModel);
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

    const selectModel = (provider, model) => {
        setSelectedModel({ provider, model });
        setIsModelMenuOpen(false);
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const uploadId = addUpload(file);

        try {
            // 1. Get presigned URL from backend
            const presignedResponse = await axios.post('http://localhost:8000/files/presigned-url', {
                filename: file.name,
                content_type: file.type
            });

            const { upload_url, file_key } = presignedResponse.data;

            // 2. Upload to MinIO using fetch to ensure ABSOLUTELY NO interceptors or headers are added
            // We use credentials: 'omit' to ensure no cookies or auth headers are sent
            const uploadResponse = await fetch(upload_url, {
                method: 'PUT',
                headers: {
                    'Content-Type': file.type
                },
                body: file,
                credentials: 'omit'
            });

            if (!uploadResponse.ok) {
                throw new Error(`Upload failed with status ${uploadResponse.status}`);
            }

            // Since fetch doesn't support progress, we just set it to 100% on success
            updateUploadProgress(uploadId, 100);

            // 3. Confirm upload with backend (triggers orchestration)
            await axios.post('http://localhost:8000/files/confirm-upload', {
                file_key,
                filename: file.name,
                session_id: 'current-session-id', // TODO: Get from context
                content_type: file.type
            });

            setUploadSuccess(uploadId);
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
            {/* Model Selector */}
            {availableProviders.length > 0 ? (
                <div className="relative">
                    <button
                        type="button"
                        onClick={() => setIsModelMenuOpen(!isModelMenuOpen)}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-secondary hover:bg-secondary/80 rounded-md transition-colors"
                    >
                        <span className="text-muted-foreground">Model:</span>
                        <span className="font-medium">
                            {selectedModel && modelConfigs[selectedModel.provider]
                                ? `${modelConfigs[selectedModel.provider].name} - ${selectedModel.model.name}`
                                : 'Select Model'}
                        </span>
                        <ChevronDown size={16} className={cn("transition-transform", isModelMenuOpen && "rotate-180")} />
                    </button>

                    {isModelMenuOpen && (
                        <div className="absolute bottom-full left-0 mb-2 bg-background border border-border rounded-lg shadow-lg overflow-hidden min-w-[250px] z-10">
                            {availableProviders.map(provider => {
                                const config = modelConfigs[provider];
                                if (!config) return null;

                                return (
                                    <div key={provider}>
                                        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-secondary/50">
                                            {config.name}
                                        </div>
                                        {config.models.map(model => (
                                            <button
                                                key={model.id}
                                                onClick={() => selectModel(provider, model)}
                                                className={cn(
                                                    "w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors",
                                                    selectedModel?.model.id === model.id && "bg-primary/10 text-primary"
                                                )}
                                            >
                                                {model.name}
                                            </button>
                                        ))}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            ) : (
                <div className="px-3 py-1.5 text-sm text-muted-foreground bg-secondary/50 rounded-md">
                    No API keys configured. Add keys in Settings to enable LLM models.
                </div>
            )}

            {/* Message Input */}
            <form onSubmit={handleSubmit} className="relative flex items-end gap-2 p-2 border border-input rounded-xl bg-background shadow-sm focus-within:ring-1 focus-within:ring-ring">
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
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
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
                    className="flex-1 max-h-[200px] py-2 bg-transparent border-none focus:ring-0 resize-none placeholder:text-muted-foreground scrollbar-hide"
                    rows={1}
                />

                <div className="flex gap-1">
                    <button
                        type="button"
                        className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        type="submit"
                        disabled={!input.trim() || availableProviders.length === 0}
                        className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </form>
        </div>
    );
};

export default MessageInput;
