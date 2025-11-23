import React, { useEffect, useRef } from 'react';
import MessageItem from './MessageItem';

const MessageList = ({ messages }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="space-y-6">
            {messages.map((msg) => (
                <MessageItem key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
        </div>
    );
};

export default MessageList;
