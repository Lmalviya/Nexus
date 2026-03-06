import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, Copy, RefreshCw, Edit2, Check, FileText } from 'lucide-react';
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
            "flex gap-4 max-w-3xl mx-auto group py-4",
            isUser ? "flex-row-reverse" : "flex-row"
        )}>
            <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                isUser ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-200"
            )}>
                {isUser ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div className={cn(
                "flex-1 min-w-0 space-y-2",
                isUser ? "text-right" : "text-left"
            )}>
                <div className="flex items-center gap-2 mb-1 justify-end">
                    <span className="text-xs text-gray-400 font-medium">
                        {isUser ? 'You' : 'Nexus'}
                    </span>
                    {message.model && (
                        <span className="text-[10px] bg-gray-800 px-1.5 py-0.5 rounded text-gray-400 uppercase border border-gray-700">
                            {message.model}
                        </span>
                    )}
                </div>

                {/* Image Rendering */}
                {message.images && message.images.length > 0 && (
                    <div className={cn("flex flex-wrap gap-2 mb-2", isUser && "justify-end")}>
                        {message.images.map((img, idx) => (
                            <img
                                key={idx}
                                src={img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}`}
                                alt="User upload"
                                className="max-w-[200px] max-h-[200px] rounded-lg border border-gray-700 object-cover"
                            />
                        ))}
                    </div>
                )}

                {isEditing ? (
                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 space-y-3">
                        <textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full bg-transparent border-none focus:ring-0 resize-none min-h-[100px] text-sm text-gray-200"
                        />
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-3 py-1.5 text-xs bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveEdit}
                                className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-500"
                            >
                                Save & Submit
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className={cn(
                        "prose prose-sm dark:prose-invert max-w-none break-words relative",
                        isUser
                            ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2 inline-block text-left"
                            : "text-gray-300"
                    )}>
                        {isUser ? (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                        ) : (
                            <ReactMarkdown
                                components={{
                                    code({ node, inline, className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '')
                                        return !inline && match ? (
                                            <SyntaxHighlighter
                                                {...props}
                                                style={vscDarkPlus}
                                                language={match[1]}
                                                PreTag="div"
                                                className="rounded-md !bg-gray-900 !p-4 my-4"
                                            >
                                                {String(children).replace(/\n$/, '')}
                                            </SyntaxHighlighter>
                                        ) : (
                                            <code {...props} className={cn("bg-gray-800 px-1.5 py-0.5 rounded text-sm", className)}>
                                                {children}
                                            </code>
                                        )
                                    }
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        )}
                    </div>
                )}

                {/* Retrieval Sources */}
                {!isUser && message.retrieval_sources && message.retrieval_sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                        {message.retrieval_sources.map((source, idx) => (
                            <div key={idx} className="flex items-center gap-1 text-xs text-gray-500 bg-gray-800/50 px-2 py-1 rounded border border-gray-700/50">
                                <FileText size={10} />
                                <span className="truncate max-w-[150px]">{source}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Action Buttons */}
                {!isEditing && (
                    <div className={cn(
                        "flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-1",
                        isUser ? "justify-end" : "justify-start"
                    )}>
                        {isUser ? (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-1 text-gray-500 hover:text-gray-300 rounded"
                                title="Edit message"
                            >
                                <Edit2 size={14} />
                            </button>
                        ) : (
                            <>
                                <button
                                    onClick={handleCopy}
                                    className="p-1 text-gray-500 hover:text-gray-300 rounded"
                                    title="Copy"
                                >
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                                <button
                                    onClick={onRegenerate}
                                    className="p-1 text-gray-500 hover:text-gray-300 rounded"
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
