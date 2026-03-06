import React, { useState, useEffect } from 'react';
import { MessageSquarePlus, Settings, MessageSquare, User, LogOut, ChevronDown, Trash2, Edit2, Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';
import { useConversation } from '../context/ConversationContext';
import SettingsModal from './Settings/SettingsModal';
import UserProfileModal from './UserProfileModal';

const Sidebar = ({ className }) => {
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editTitle, setEditTitle] = useState('');

    const { user, logout } = useAuth();
    const {
        sessions,
        currentSessionId,
        fetchSessions,
        loadSession,
        clearCurrentSession,
        deleteSession,
        updateSessionTitle
    } = useConversation();

    const navigate = useNavigate();

    useEffect(() => {
        fetchSessions();
    }, [fetchSessions]);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleNewChat = () => {
        clearCurrentSession();
    };

    const handleEditTitle = (session, e) => {
        e.stopPropagation();
        setEditingSessionId(session.session_id);
        setEditTitle(session.title);
    };

    const saveTitle = async (sessionId, e) => {
        e.stopPropagation();
        if (editTitle.trim()) {
            await updateSessionTitle(sessionId, editTitle);
        }
        setEditingSessionId(null);
    };

    const cancelEdit = (e) => {
        e.stopPropagation();
        setEditingSessionId(null);
    };

    const handleDeleteSession = async (sessionId, e) => {
        e.stopPropagation();
        if (confirm('Are you sure you want to delete this chat?')) {
            await deleteSession(sessionId);
        }
    };

    return (
        <>
            <div className={cn("flex flex-col h-full w-64 bg-secondary/30 border-r border-border p-4", className)}>
                <div className="mb-6">
                    <button
                        onClick={handleNewChat}
                        className="flex items-center justify-center w-full gap-2 px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
                    >
                        <MessageSquarePlus size={18} />
                        New Chat
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    <h3 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Recents
                    </h3>
                    <div className="space-y-1">
                        {sessions.length === 0 ? (
                            <div className="text-xs text-muted-foreground px-2 py-4 text-center">
                                No conversations yet
                            </div>
                        ) : (
                            sessions.map((session) => (
                                <div
                                    key={session.session_id}
                                    onClick={() => loadSession(session.session_id)}
                                    className={cn(
                                        "group flex items-center w-full gap-2 px-3 py-2 text-sm text-left rounded-md cursor-pointer transition-colors",
                                        currentSessionId === session.session_id
                                            ? "bg-accent text-accent-foreground"
                                            : "hover:bg-accent/50 hover:text-accent-foreground"
                                    )}
                                >
                                    <MessageSquare size={16} className="text-muted-foreground flex-shrink-0" />

                                    {editingSessionId === session.session_id ? (
                                        <div className="flex items-center flex-1 gap-1 min-w-0">
                                            <input
                                                type="text"
                                                value={editTitle}
                                                onChange={(e) => setEditTitle(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="w-full bg-background border border-primary rounded px-1 py-0.5 text-xs focus:outline-none"
                                                autoFocus
                                            />
                                            <button onClick={(e) => saveTitle(session.session_id, e)} className="text-green-500 hover:text-green-600">
                                                <Check size={14} />
                                            </button>
                                            <button onClick={cancelEdit} className="text-red-500 hover:text-red-600">
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            <span className="truncate flex-1">{session.title}</span>

                                            <div className="hidden group-hover:flex items-center gap-1">
                                                <button
                                                    onClick={(e) => handleEditTitle(session, e)}
                                                    className="p-1 text-muted-foreground hover:text-foreground rounded"
                                                    title="Rename"
                                                >
                                                    <Edit2 size={12} />
                                                </button>
                                                <button
                                                    onClick={(e) => handleDeleteSession(session.session_id, e)}
                                                    className="p-1 text-muted-foreground hover:text-red-500 rounded"
                                                    title="Delete"
                                                >
                                                    <Trash2 size={12} />
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="mt-auto pt-4 border-t border-border space-y-2">
                    {/* User Profile Menu */}
                    <div className="relative">
                        <button
                            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                            className="flex items-center w-full gap-2 px-3 py-2 text-sm text-left rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                                <User size={16} className="text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{user?.full_name || 'User'}</p>
                                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                            </div>
                            <ChevronDown size={14} className="text-muted-foreground" />
                        </button>

                        {isUserMenuOpen && (
                            <div className="absolute bottom-full left-0 w-full mb-2 bg-popover border border-border rounded-md shadow-lg py-1 z-50 animate-in fade-in zoom-in-95 duration-200">
                                <button
                                    onClick={() => {
                                        setIsProfileOpen(true);
                                        setIsUserMenuOpen(false);
                                    }}
                                    className="flex items-center w-full gap-2 px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                                >
                                    <User size={16} />
                                    View Profile
                                </button>
                                <button
                                    onClick={() => {
                                        setIsSettingsOpen(true);
                                        setIsUserMenuOpen(false);
                                    }}
                                    className="flex items-center w-full gap-2 px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                                >
                                    <Settings size={16} />
                                    Settings
                                </button>
                                <div className="h-px bg-border my-1" />
                                <button
                                    onClick={handleLogout}
                                    className="flex items-center w-full gap-2 px-4 py-2 text-sm text-red-500 hover:bg-red-500/10"
                                >
                                    <LogOut size={16} />
                                    Sign Out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
            <UserProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
        </>
    );
};

export default Sidebar;
