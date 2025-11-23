import React from 'react';
import { Code, FileText, Image as ImageIcon } from 'lucide-react';

const ArtifactPanel = () => {
    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="text-sm font-semibold uppercase tracking-wider">Artifacts</h2>
                <div className="flex gap-2">
                    {/* Tabs or filters could go here */}
                </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
                    <div className="p-4 rounded-full bg-secondary/50">
                        <FileText size={32} />
                    </div>
                    <p className="text-sm">Generated content will appear here</p>
                </div>
            </div>
        </div>
    );
};

export default ArtifactPanel;
