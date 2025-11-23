import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import { cn } from '../../utils/cn';

const MessageItem = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={cn(
            "flex gap-4 max-w-3xl mx-auto",
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
                <div className="text-xs text-muted-foreground font-medium">
                    {isUser ? 'You' : 'Nexus'}
                </div>

                <div className={cn(
                    "prose prose-sm dark:prose-invert max-w-none break-words",
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
            </div>
        </div>
    );
};

export default MessageItem;
