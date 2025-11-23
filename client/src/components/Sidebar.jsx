import React from 'react';
import { MessageSquarePlus, Settings, History, MessageSquare } from 'lucide-react';
import { cn } from '../utils/cn'; // We'll need a utility for class merging

const Sidebar = ({ className }) => {
    return (
        <div className={cn("flex flex-col h-full w-64 bg-secondary/30 border-r border-border p-4", className)}>
            <div className="mb-6">
                <button className="flex items-center justify-center w-full gap-2 px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors">
                    <MessageSquarePlus size={18} />
                    New Chat
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                <h3 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Recents
                </h3>
                <div className="space-y-1">
                    {/* Mock History Items */}
                    {['Project Nexus Planning', 'React Component Structure', 'Tailwind Config Help'].map((item, index) => (
                        <button
                            key={index}
                            className="flex items-center w-full gap-2 px-3 py-2 text-sm text-left rounded-md hover:bg-accent hover:text-accent-foreground transition-colors group"
                        >
                            <MessageSquare size={16} className="text-muted-foreground group-hover:text-foreground" />
                            <span className="truncate">{item}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="mt-auto pt-4 border-t border-border">
                <button className="flex items-center w-full gap-2 px-3 py-2 text-sm text-left rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                    <Settings size={18} />
                    <span>Settings</span>
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
