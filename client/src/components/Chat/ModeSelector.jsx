import React, { useState } from 'react';
import { ChevronDown, Zap, Brain, Globe, Database } from 'lucide-react';

const modes = [
    { id: 'standard', name: 'Standard Chat', icon: Zap, description: 'Fast, general purpose' },
    { id: 'deep-thinker', name: 'Deep Thinker', icon: Brain, description: 'Uses reasoning models' },
    { id: 'deep-research', name: 'Deep Research', icon: Globe, description: 'Browses the web autonomously' },
    { id: 'data', name: 'Talk with Data', icon: Database, description: 'RAG specific analysis' },
];

const ModeSelector = ({ currentMode, onModeChange }) => {
    const [isOpen, setIsOpen] = useState(false);

    const selectedMode = modes.find(m => m.id === currentMode) || modes[0];
    const Icon = selectedMode.icon;

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border"
            >
                <Icon size={16} className="text-primary" />
                <span>{selectedMode.name}</span>
                <ChevronDown size={14} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute top-full left-0 mt-1 w-64 p-1 bg-popover text-popover-foreground border border-border rounded-md shadow-md z-20 animate-in fade-in zoom-in-95 duration-100">
                        {modes.map((mode) => {
                            const ModeIcon = mode.icon;
                            return (
                                <button
                                    key={mode.id}
                                    onClick={() => {
                                        onModeChange(mode.id);
                                        setIsOpen(false);
                                    }}
                                    className={`flex items-start w-full gap-3 px-3 py-2 text-left rounded-sm hover:bg-accent hover:text-accent-foreground transition-colors ${currentMode === mode.id ? 'bg-accent/50' : ''
                                        }`}
                                >
                                    <ModeIcon size={18} className="mt-0.5 text-primary" />
                                    <div>
                                        <div className="text-sm font-medium">{mode.name}</div>
                                        <div className="text-xs text-muted-foreground">{mode.description}</div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </>
            )}
        </div>
    );
};

export default ModeSelector;
