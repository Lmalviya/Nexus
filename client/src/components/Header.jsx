import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Header = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handlePlaygroundClick = () => {
        if (user) {
            navigate('/chat');
        } else {
            navigate('/login');
        }
    };

    return (
        <header className="bg-gray-800 border-b border-gray-700 py-4 px-6 flex justify-between items-center">
            <div className="flex items-center space-x-8">
                <Link to="/" className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Nexus
                </Link>
                <button
                    onClick={handlePlaygroundClick}
                    className="text-gray-300 hover:text-white transition-colors font-medium"
                >
                    Playground
                </button>
            </div>

            <div>
                {user ? (
                    <div className="flex items-center space-x-4">
                        <span className="text-gray-400 text-sm">Welcome, {user.full_name}</span>
                        <button
                            onClick={() => {
                                logout();
                                navigate('/');
                            }}
                            className="text-sm bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                ) : (
                    <Link
                        to="/login"
                        className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
                    >
                        Sign In
                    </Link>
                )}
            </div>
        </header>
    );
};

export default Header;
