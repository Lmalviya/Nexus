import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import Footer from '../components/Footer';

const Login = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await axios.post('http://localhost:8000/auth/login', {
                email,
                password
            });

            if (res.data.status === 'success') {
                login(res.data.user, res.data.token);
                navigate('/chat');
            }
        } catch (err) {
            console.error("Login Failed", err);
            setError(err.response?.data?.detail || "Login failed. Please check your credentials.");
        }
    };

    return (
        <div className="flex flex-col min-h-screen bg-gray-900">
            <Header />
            <div className="flex-grow flex items-center justify-center">
                <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md">
                    <h2 className="text-3xl font-bold text-white mb-6 text-center">Sign In</h2>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-2 rounded mb-4 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-gray-300 mb-1">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-gray-300 mb-1">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded mt-4 transition-colors"
                        >
                            Sign In
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-gray-400 text-sm">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-blue-400 hover:text-blue-300">
                                Register here
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default Login;
