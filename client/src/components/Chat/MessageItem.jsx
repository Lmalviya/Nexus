import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, Copy, RefreshCw, Edit2, Check, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const MessageItem = ({ message, onEdit, onRegenerate }) => {
    const isUser = message.role === 'user';
    const [isEditing, setIsEditing] = useState(false);
    const [editContent, setEditContent] = useState(message.content);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleSaveEdit = () => {
        if (editContent.trim() !== message.content) {
            onEdit(message.id, editContent);
        }
        setIsEditing(false);
    };

    return (
        <div className={cn(
            "flex gap-4 max-w-3xl mx-auto group",
            isUser ? "flex-row-reverse" : "flex-row"
        )}>
            <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
            )}>
                {isUser ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div className={cn(
                "flex-1 min-w-0 space-y-2",
                isUser ? "text-right" : "text-left"
            )}>
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-muted-foreground font-medium">
                        {isUser ? 'You' : 'Nexus'}
                    </span>
                    {message.model && (
                        <span className="text-[10px] bg-secondary px-1.5 py-0.5 rounded text-muted-foreground uppercase">
                            {message.model}
                        </span>
                    )}
                </div>

                {isEditing ? (
                    <div className="bg-background border border-border rounded-lg p-3 space-y-3">
                        <textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full bg-transparent border-none focus:ring-0 resize-none min-h-[100px] text-sm"
                        />
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-3 py-1.5 text-xs bg-secondary text-foreground rounded-md hover:bg-secondary/80"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveEdit}
                                className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                            >
                                Save & Submit
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className={cn(
                        "prose prose-sm dark:prose-invert max-w-none break-words relative",
                        isUser ? "bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2 inline-block text-left" : ""
                    )}>
                        {isUser ? (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                        ) : (
                            <ReactMarkdown>
                                {message.content}
                            </ReactMarkdown>
                        )}
                    </div>
                )}

                {/* Action Buttons */}
                {!isEditing && (
                    <div className={cn(
                        "flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity",
                        isUser ? "justify-end" : "justify-start"
                    )}>
                        {isUser ? (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-1 text-muted-foreground hover:text-foreground rounded"
                                title="Edit message"
                            >
                                <Edit2 size={14} />
                            </button>
                        ) : (
                            <>
                                <button
                                    onClick={handleCopy}
                                    className="p-1 text-muted-foreground hover:text-foreground rounded"
                                    title="Copy"
                                >
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                                <button
                                    onClick={onRegenerate}
                                    className="p-1 text-muted-foreground hover:text-foreground rounded"
                                    title="Regenerate response"
                                >
                                    <RefreshCw size={14} />
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageItem;
