import React, { useState, useEffect } from 'react';
import ModeSelector from './ModeSelector';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { useConversation } from '../../context/ConversationContext';
import { useAuth } from '../../context/AuthContext';
import { MessageSquarePlus } from 'lucide-react';

const ChatInterface = () => {
    const [mode, setMode] = useState('standard');
    const {
        currentSessionId,
        messages,
        sendMessage,
        loading,
        modifyMessage,
        regenerateResponse
    } = useConversation();
    const { user } = useAuth();

    const handleSendMessage = (content, model) => {
        sendMessage(content, model?.model, model?.provider);
    };

    return (
        <div className="flex flex-col h-full w-full max-w-4xl mx-auto relative">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
                <ModeSelector currentMode={mode} onModeChange={setMode} />
                <div className="text-xs text-muted-foreground">
                    {messages.length} messages
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                {!currentSessionId && messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-0 animate-in fade-in duration-700 slide-in-from-bottom-4">
                        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                            <MessageSquarePlus size={40} className="text-primary" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold mb-2">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}! 👋</h2>
                            <p className="text-muted-foreground max-w-md">
                                I'm Nexus, your AI assistant. Start a new conversation to get help with coding, writing, analysis, and more.
                            </p>
                        </div>
                        <div className="grid grid-cols-2 gap-4 max-w-lg w-full mt-8">
                            {['Explain quantum computing', 'Write a Python script', 'Debug my React code', 'Draft an email'].map((prompt, i) => (
                                <button
                                    key={i}
                                    onClick={() => handleSendMessage(prompt, null)}
                                    className="p-4 border border-border rounded-xl hover:bg-accent hover:border-primary/50 transition-all text-sm text-left"
                                >
                                    {prompt}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <MessageList
                        messages={messages}
                        onEdit={modifyMessage}
                        onRegenerate={regenerateResponse}
                    />
                )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border bg-background">
                <MessageInput onSendMessage={handleSendMessage} />
            </div>
        </div>
    );
};

export default ChatInterface;
