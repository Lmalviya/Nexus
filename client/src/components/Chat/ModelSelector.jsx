import React, { useState, useEffect } from 'react';
import { useConversation } from '../../context/ConversationContext';

const ModelSelector = () => {
    const { currentModel, setModel, availableModels } = useConversation();
    const [isOpen, setIsOpen] = useState(false);

    // Default models if none provided
    const models = availableModels || [
        { id: 'gpt-4', name: 'GPT-4', provider: 'openai' },
        { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'openai' },
        { id: 'claude-3-opus', name: 'Claude 3 Opus', provider: 'anthropic' },
        { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', provider: 'anthropic' },
        { id: 'llama3', name: 'Llama 3 (Local)', provider: 'ollama' },
        { id: 'mistral', name: 'Mistral (Local)', provider: 'ollama' }
    ];

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center space-x-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700 text-sm font-medium text-gray-200"
            >
                <span>{models.find(m => m.id === currentModel?.id)?.name || 'Select Model'}</span>
                <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute top-full mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-20 overflow-hidden">
                        <div className="py-1">
                            {models.map((model) => (
                                <button
                                    key={`${model.provider}-${model.id}`}
                                    onClick={() => {
                                        setModel(model);
                                        setIsOpen(false);
                                    }}
                                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors flex items-center justify-between
                    ${currentModel?.id === model.id ? 'bg-gray-700/50 text-blue-400' : 'text-gray-300'}
                  `}
                                >
                                    <span>{model.name}</span>
                                    {currentModel?.id === model.id && (
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default ModelSelector;
