import React, { useState } from 'react';
import Sidebar from './Sidebar';
import ArtifactPanel from './Artifacts/ArtifactPanel';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';

const Layout = ({ children }) => {
    const [isArtifactPanelOpen, setIsArtifactPanelOpen] = useState(false);

    return (
        <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
            <Sidebar />

            <main className="flex-1 flex flex-col min-w-0 relative transition-all duration-300 ease-in-out">
                {children}

                {/* Toggle Artifact Panel Button (Floating or in header, putting it absolute for now) */}
                <button
                    onClick={() => setIsArtifactPanelOpen(!isArtifactPanelOpen)}
                    className="absolute top-4 right-4 z-10 p-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors shadow-sm"
                    title={isArtifactPanelOpen ? "Close Artifacts" : "Open Artifacts"}
                >
                    {isArtifactPanelOpen ? <PanelRightClose size={20} /> : <PanelRightOpen size={20} />}
                </button>
            </main>

            {/* Artifact Panel */}
            <div
                className={`border-l border-border bg-card transition-all duration-300 ease-in-out ${isArtifactPanelOpen ? 'w-[400px] translate-x-0' : 'w-0 translate-x-full opacity-0'
                    }`}
            >
                <div className="w-[400px] h-full">
                    <ArtifactPanel />
                </div>
            </div>
        </div>
    );
};

export default Layout;
