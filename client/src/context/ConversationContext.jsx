import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';

const ConversationContext = createContext();

export const useConversation = () => useContext(ConversationContext);

export const ConversationProvider = ({ children }) => {
    const [sessions, setSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);

    // Fetch all sessions
    const fetchSessions = useCallback(async () => {
        try {
            const response = await axios.get('http://localhost:8000/conversations');
            setSessions(response.data.sessions || []);
        } catch (error) {
            console.error('Failed to fetch sessions:', error);
        }
    }, []);

    // Load a specific session
    const loadSession = useCallback(async (sessionId) => {
        if (!sessionId) {
            setCurrentSessionId(null);
            setMessages([]);
            return;
        }

        setLoading(true);
        try {
            const response = await axios.get(`http://localhost:8000/conversations/${sessionId}`);
            setCurrentSessionId(sessionId);
            setMessages(response.data.session.messages || []);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Create a new session
    const createSession = async (title = null) => {
        try {
            const response = await axios.post('http://localhost:8000/conversations', { title });
            const newSession = response.data.session;
            setSessions(prev => [
                {
                    session_id: newSession.session_id,
                    title: newSession.title,
                    updated_at: newSession.updated_at
                },
                ...prev
            ]);
            setCurrentSessionId(newSession.session_id);
            setMessages([]);
            return newSession.session_id;
        } catch (error) {
            console.error('Failed to create session:', error);
            return null;
        }
    };

    // Send a message
    const sendMessage = async (content, model, provider) => {
        let sessionId = currentSessionId;

        // If no session exists, create one first
        if (!sessionId) {
            sessionId = await createSession();
            if (!sessionId) return;
        }

        // Optimistically add user message
        const userMsg = {
            id: Date.now().toString(), // Temporary ID
            role: 'user',
            content,
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMsg]);
        setStreaming(true);

        try {
            // Send user message to backend
            const response = await axios.post(`http://localhost:8000/conversations/${sessionId}/messages`, {
                role: 'user',
                content,
                model: model?.id,
                provider: provider,
                input_tokens: 0 // Backend/LLM will calculate this later
            });

            // Update messages with real data from backend
            setMessages(response.data.session.messages);

            // Refresh session list to update title/timestamp
            fetchSessions();

            // Simulate AI response (since we don't have real LLM connected yet)
            // In a real app, this would be a separate call or streaming response
            setTimeout(async () => {
                const aiResponse = await axios.post(`http://localhost:8000/conversations/${sessionId}/messages`, {
                    role: 'assistant',
                    content: `This is a simulated response from ${model?.name || 'Nexus AI'}. I received: "${content}"`,
                    model: model?.id,
                    provider: provider,
                    output_tokens: 50 // Dummy token count
                });
                setMessages(aiResponse.data.session.messages);
                setStreaming(false);
                fetchSessions();
            }, 1000);

        } catch (error) {
            console.error('Failed to send message:', error);
            setStreaming(false);
        }
    };
    // Edit a message
    const modifyMessage = async (messageId, newContent) => {
        try {
            // Optimistic update
            const updatedMessages = messages.map(msg =>
                msg.id === messageId ? { ...msg, content: newContent } : msg
            );
            // Truncate messages after the edited one (ChatGPT style)
            const msgIndex = updatedMessages.findIndex(m => m.id === messageId);
            const truncatedMessages = updatedMessages.slice(0, msgIndex + 1);

            setMessages(truncatedMessages);

            // Find the message to get its model/provider
            const messageToEdit = messages.find(m => m.id === messageId);
            const modelToUse = messageToEdit?.model;
            const providerToUse = messageToEdit?.provider;

            await axios.delete(`http://localhost:8000/conversations/${currentSessionId}/messages/${messageId}`);

            // Re-send the message to generate a new response
            await sendMessage(newContent, modelToUse, providerToUse);
        } catch (error) {
            console.error('Failed to edit message:', error);
            // Revert on error (reload session)
            if (currentSessionId) {
                loadSession(currentSessionId);
            }
        }
    };

    // Regenerate response
    const regenerateResponse = async () => {
        if (!currentSessionId) return;

        try {
            setStreaming(true);
            // 1. Call regenerate endpoint (deletes last assistant message)
            const regResponse = await axios.post(`http://localhost:8000/conversations/${currentSessionId}/regenerate`);

            // 2. Update local state immediately to remove the old assistant message
            const currentMessages = regResponse.data.session.messages;
            setMessages(currentMessages);

            // 3. Get the last user message to re-send to LLM
            const lastUserMsg = currentMessages[currentMessages.length - 1];

            if (lastUserMsg && lastUserMsg.role === 'user') {
                // Simulate AI response again
                setTimeout(async () => {
                    const aiResponse = await axios.post(`http://localhost:8000/conversations/${currentSessionId}/messages`, {
                        role: 'assistant',
                        content: `Regenerated response for: "${lastUserMsg.content}"`,
                        model: lastUserMsg.model,
                        provider: lastUserMsg.provider,
                        output_tokens: 55
                    });
                    setMessages(aiResponse.data.session.messages);
                    setStreaming(false);
                    fetchSessions();
                }, 1000);
            } else {
                setStreaming(false);
            }

        } catch (error) {
            console.error('Failed to regenerate:', error);
            setStreaming(false);
        }
    };

    // Delete a session
    const deleteSession = async (sessionId) => {
        try {
            await axios.delete(`http://localhost:8000/conversations/${sessionId}`);
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    // Update session title
    const updateSessionTitle = async (sessionId, newTitle) => {
        try {
            await axios.put(`http://localhost:8000/conversations/${sessionId}/title`, { title: newTitle });
            setSessions(prev => prev.map(s =>
                s.session_id === sessionId ? { ...s, title: newTitle } : s
            ));
        } catch (error) {
            console.error('Failed to update session title:', error);
        }
    };

    const clearCurrentSession = () => {
        setCurrentSessionId(null);
        setMessages([]);
    };

    return (
        <ConversationContext.Provider value={{
            sessions,
            currentSessionId,
            messages,
            loading,
            streaming,
            fetchSessions,
            loadSession,
            createSession,
            sendMessage,
            modifyMessage,
            regenerateResponse,
            deleteSession,
            updateSessionTitle,
            clearCurrentSession
        }}>
            {children}
        </ConversationContext.Provider>
    );
};
