import React, { useState } from 'react';
import ModeSelector from './ModeSelector';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatInterface = () => {
    const [mode, setMode] = useState('standard');
    const [messages, setMessages] = useState([
        {
            id: 1,
            role: 'assistant',
            content: 'Hello! I am Nexus. How can I help you today?',
            timestamp: new Date().toISOString(),
        }
    ]);

    const handleSendMessage = (content) => {
        const newMessage = {
            id: Date.now(),
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };
        setMessages([...messages, newMessage]);

        // Simulate response
        setTimeout(() => {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: 'I received your message. This is a mock response.',
                timestamp: new Date().toISOString(),
            }]);
        }, 1000);
    };

    return (
        <div className="flex flex-col h-full w-full max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
                <ModeSelector currentMode={mode} onModeChange={setMode} />
                <div className="text-xs text-muted-foreground">
                    {messages.length} messages
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                <MessageList messages={messages} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border bg-background">
                <MessageInput onSendMessage={handleSendMessage} />
            </div>
        </div>
    );
};

export default ChatInterface;
