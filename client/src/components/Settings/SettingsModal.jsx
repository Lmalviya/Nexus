import React from 'react';
import { X, Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

const SettingsModal = ({ isOpen, onClose }) => {
    const { theme, setTheme } = useTheme();

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-background border border-border rounded-xl shadow-lg animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <h2 className="text-lg font-semibold">Settings</h2>
                    <button onClick={onClose} className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    <div>
                        <h3 className="text-sm font-medium mb-3 text-muted-foreground uppercase tracking-wider">Appearance</h3>
                        <div className="grid grid-cols-3 gap-4">
                            <button
                                onClick={() => setTheme('light')}
                                className={cn(
                                    "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                    theme === 'light'
                                        ? "border-primary bg-primary/5"
                                        : "border-transparent bg-secondary hover:bg-secondary/80"
                                )}
                            >
                                <Sun size={24} />
                                <span className="text-sm font-medium">Light</span>
                            </button>

                            <button
                                onClick={() => setTheme('dark')}
                                className={cn(
                                    "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                    theme === 'dark'
                                        ? "border-primary bg-primary/5"
                                        : "border-transparent bg-secondary hover:bg-secondary/80"
                                )}
                            >
                                <Moon size={24} />
                                <span className="text-sm font-medium">Dark</span>
                            </button>

                            <button
                                onClick={() => setTheme('system')}
                                className={cn(
                                    "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                    theme === 'system'
                                        ? "border-primary bg-primary/5"
                                        : "border-transparent bg-secondary hover:bg-secondary/80"
                                )}
                            >
                                <Monitor size={24} />
                                <span className="text-sm font-medium">System</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
