import React from 'react';
import { X, User, Mail, Building, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const UserProfileModal = ({ isOpen, onClose }) => {
    const { user } = useAuth();

    if (!isOpen || !user) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-background border border-border rounded-xl shadow-lg animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <h2 className="text-lg font-semibold">Profile</h2>
                    <button onClick={onClose} className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                            <User size={32} className="text-primary" />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold">{user.full_name}</h3>
                            <p className="text-sm text-muted-foreground capitalize">{user.role}</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50">
                            <Mail size={18} className="text-muted-foreground" />
                            <div>
                                <p className="text-xs text-muted-foreground">Email</p>
                                <p className="text-sm">{user.email}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50">
                            <Shield size={18} className="text-muted-foreground" />
                            <div>
                                <p className="text-xs text-muted-foreground">Role</p>
                                <p className="text-sm capitalize">{user.role}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50">
                            <Building size={18} className="text-muted-foreground" />
                            <div>
                                <p className="text-xs text-muted-foreground">Organization ID</p>
                                <p className="text-sm font-mono text-xs">{user.organization_id || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserProfileModal;
