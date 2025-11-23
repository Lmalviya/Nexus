import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import Footer from '../components/Footer';

const Home = () => {
    const navigate = useNavigate();
    const { user } = useAuth();

    return (
        <div className="flex flex-col min-h-screen bg-gray-900 text-white">
            <Header />
            <div className="flex-grow flex flex-col items-center justify-center">
                <h1 className="text-5xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Welcome to Nexus
                </h1>
                <p className="text-xl text-gray-400 mb-12 max-w-2xl text-center">
                    The advanced AI coding assistant platform for your organization.
                </p>

                <div className="space-x-4">
                    {user ? (
                        <button
                            onClick={() => navigate('/chat')}
                            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                        >
                            Go to Chat
                        </button>
                    ) : (
                        <button
                            onClick={() => navigate('/login')}
                            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                        >
                            Get Started
                        </button>
                    )}
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default Home;
