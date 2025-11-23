import React, { useState, useEffect } from 'react';
import { X, Moon, Sun, Monitor, Plus, Trash2, BarChart3, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

const SettingsModal = ({ isOpen, onClose }) => {
    const { theme, setTheme } = useTheme();
    const [activeTab, setActiveTab] = useState('appearance');

    // API Keys state
    const [apiKeys, setApiKeys] = useState([]);
    const [showAddForm, setShowAddForm] = useState(false);
    const [newKey, setNewKey] = useState({ provider: '', key: '', name: '' });
    const [showKeys, setShowKeys] = useState({});
    const [usageView, setUsageView] = useState(null);
    const [loading, setLoading] = useState(false);

    // Available providers
    const availableProviders = [
        { id: 'openai', name: 'OpenAI', placeholder: 'sk-...' },
        { id: 'claude', name: 'Claude (Anthropic)', placeholder: 'sk-ant-...' },
        { id: 'gemini', name: 'Google Gemini', placeholder: 'AI...' },
        { id: 'cohere', name: 'Cohere', placeholder: 'co-...' },
        { id: 'huggingface', name: 'HuggingFace', placeholder: 'hf_...' },
        { id: 'mistral', name: 'Mistral AI', placeholder: 'mis-...' }
    ];

    // Load API keys from backend
    useEffect(() => {
        if (isOpen && activeTab === 'apikeys') {
            fetchApiKeys();
        }
    }, [isOpen, activeTab]);

    const fetchApiKeys = async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://localhost:8000/api-keys');
            setApiKeys(response.data.keys || []);
        } catch (error) {
            console.error('Failed to fetch API keys:', error);
            alert('Failed to load API keys');
        } finally {
            setLoading(false);
        }
    };

    const handleAddKey = async () => {
        if (!newKey.provider || !newKey.key) {
            alert('Please select a provider and enter an API key');
            return;
        }

        setLoading(true);
        try {
            await axios.post('http://localhost:8000/api-keys', {
                provider: newKey.provider,
                key_name: newKey.name || `${availableProviders.find(p => p.id === newKey.provider)?.name} Key`,
                api_key: newKey.key
            });

            setNewKey({ provider: '', key: '', name: '' });
            setShowAddForm(false);
            await fetchApiKeys();
            alert('API key added successfully!');
        } catch (error) {
            console.error('Failed to add API key:', error);
            alert(error.response?.data?.detail || 'Failed to add API key');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteKey = async (id) => {
        if (!confirm('Are you sure you want to delete this API key?')) return;

        setLoading(true);
        try {
            await axios.delete(`http://localhost:8000/api-keys/${id}`);
            await fetchApiKeys();
            alert('API key deleted successfully!');
        } catch (error) {
            console.error('Failed to delete API key:', error);
            alert('Failed to delete API key');
        } finally {
            setLoading(false);
        }
    };

    const toggleShowKey = (id) => {
        setShowKeys(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const showUsage = (keyObj) => {
        // Dummy usage data
        const dummyUsage = {
            totalTokens: Math.floor(Math.random() * 100000),
            requestCount: Math.floor(Math.random() * 1000),
            lastUsed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toLocaleDateString(),
            costEstimate: (Math.random() * 50).toFixed(2)
        };
        setUsageView({ ...keyObj, usage: dummyUsage });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-2xl bg-background border border-border rounded-xl shadow-lg animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <h2 className="text-lg font-semibold">Settings</h2>
                    <button onClick={onClose} className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-border">
                    <button
                        onClick={() => setActiveTab('appearance')}
                        className={cn(
                            "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
                            activeTab === 'appearance'
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        Appearance
                    </button>
                    <button
                        onClick={() => setActiveTab('apikeys')}
                        className={cn(
                            "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
                            activeTab === 'apikeys'
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        API Keys
                    </button>
                </div>

                <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
                    {activeTab === 'appearance' && (
                        <div>
                            <h3 className="text-sm font-medium mb-3 text-muted-foreground uppercase tracking-wider">Theme</h3>
                            <div className="grid grid-cols-3 gap-4">
                                <button
                                    onClick={() => setTheme('light')}
                                    className={cn(
                                        "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                        theme === 'light' ? "border-primary bg-primary/5" : "border-transparent bg-secondary hover:bg-secondary/80"
                                    )}
                                >
                                    <Sun size={24} />
                                    <span className="text-sm font-medium">Light</span>
                                </button>
                                <button
                                    onClick={() => setTheme('dark')}
                                    className={cn(
                                        "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                        theme === 'dark' ? "border-primary bg-primary/5" : "border-transparent bg-secondary hover:bg-secondary/80"
                                    )}
                                >
                                    <Moon size={24} />
                                    <span className="text-sm font-medium">Dark</span>
                                </button>
                                <button
                                    onClick={() => setTheme('system')}
                                    className={cn(
                                        "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                                        theme === 'system' ? "border-primary bg-primary/5" : "border-transparent bg-secondary hover:bg-secondary/80"
                                    )}
                                >
                                    <Monitor size={24} />
                                    <span className="text-sm font-medium">System</span>
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'apikeys' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">API Keys</h3>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Manage your LLM provider API keys (stored securely in database)
                                    </p>
                                </div>
                                <button
                                    onClick={() => setShowAddForm(!showAddForm)}
                                    disabled={loading}
                                    className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                                >
                                    <Plus size={16} />
                                    Add Key
                                </button>
                            </div>

                            {/* Add Key Form */}
                            {showAddForm && (
                                <div className="p-4 bg-secondary/50 rounded-lg space-y-3 border border-border">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Provider</label>
                                        <select
                                            value={newKey.provider}
                                            onChange={(e) => setNewKey({ ...newKey, provider: e.target.value })}
                                            className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                                        >
                                            <option value="">Select a provider...</option>
                                            {availableProviders.map(p => (
                                                <option key={p.id} value={p.id}>{p.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Key Name (Optional)</label>
                                        <input
                                            type="text"
                                            value={newKey.name}
                                            onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                                            placeholder="e.g., Production Key"
                                            className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">API Key</label>
                                        <input
                                            type="password"
                                            value={newKey.key}
                                            onChange={(e) => setNewKey({ ...newKey, key: e.target.value })}
                                            placeholder={availableProviders.find(p => p.id === newKey.provider)?.placeholder || 'Enter API key...'}
                                            className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={handleAddKey}
                                            disabled={loading}
                                            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                                        >
                                            {loading ? 'Adding...' : 'Add'}
                                        </button>
                                        <button
                                            onClick={() => {
                                                setShowAddForm(false);
                                                setNewKey({ provider: '', key: '', name: '' });
                                            }}
                                            className="px-4 py-2 bg-secondary text-foreground rounded-md hover:bg-secondary/80 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* API Keys List */}
                            <div className="space-y-2">
                                {loading && apiKeys.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        Loading...
                                    </div>
                                ) : apiKeys.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        No API keys added yet. Click "Add Key" to get started.
                                    </div>
                                ) : (
                                    apiKeys.map(keyObj => (
                                        <div key={keyObj.id} className="p-3 bg-secondary/50 rounded-lg border border-border">
                                            <div className="flex items-center justify-between mb-2">
                                                <div>
                                                    <p className="font-medium">{keyObj.key_name}</p>
                                                    <p className="text-xs text-muted-foreground capitalize">{keyObj.provider}</p>
                                                </div>
                                                <div className="flex gap-1">
                                                    <button
                                                        onClick={() => showUsage(keyObj)}
                                                        className="p-2 hover:bg-accent rounded transition-colors"
                                                        title="View Usage"
                                                    >
                                                        <BarChart3 size={16} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteKey(keyObj.id)}
                                                        disabled={loading}
                                                        className="p-2 hover:bg-red-500/10 text-red-500 rounded transition-colors disabled:opacity-50"
                                                        title="Delete Key"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="text-xs font-mono bg-background px-2 py-1 rounded">
                                                {keyObj.key_preview || '••••••••••••••••'}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Usage Modal */}
            {usageView && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-background border border-border rounded-xl shadow-lg">
                        <div className="flex items-center justify-between p-4 border-b border-border">
                            <h3 className="text-lg font-semibold">API Key Usage</h3>
                            <button onClick={() => setUsageView(null)} className="p-1 rounded-md hover:bg-accent transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <p className="text-sm text-muted-foreground">Key Name</p>
                                <p className="font-medium">{usageView.key_name}</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-3 bg-secondary/50 rounded-lg">
                                    <p className="text-xs text-muted-foreground">Total Tokens</p>
                                    <p className="text-xl font-bold">{usageView.usage.totalTokens.toLocaleString()}</p>
                                </div>
                                <div className="p-3 bg-secondary/50 rounded-lg">
                                    <p className="text-xs text-muted-foreground">Requests</p>
                                    <p className="text-xl font-bold">{usageView.usage.requestCount.toLocaleString()}</p>
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/50 rounded-lg">
                                <p className="text-xs text-muted-foreground">Estimated Cost</p>
                                <p className="text-2xl font-bold">${usageView.usage.costEstimate}</p>
                            </div>
                            <div className="p-3 bg-secondary/50 rounded-lg">
                                <p className="text-xs text-muted-foreground">Last Used</p>
                                <p className="font-medium">{usageView.usage.lastUsed}</p>
                            </div>
                            <p className="text-xs text-muted-foreground text-center">
                                Note: Usage data is currently simulated for demonstration
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SettingsModal;
