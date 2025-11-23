import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';

const MessageInput = ({ onSendMessage }) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef(null);

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
        // Auto-resize
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
    };

    return (
        <form onSubmit={handleSubmit} className="relative flex items-end gap-2 p-2 border border-input rounded-xl bg-background shadow-sm focus-within:ring-1 focus-within:ring-ring">
            <button
                type="button"
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
                {/* Voice input placeholder */}
                <button
                    type="button"
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                >
                    <Mic size={20} />
                </button>

                <button
                    type="submit"
                    disabled={!input.trim()}
                    className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <Send size={18} />
                </button>
            </div>
        </form>
    );
};

export default MessageInput;
