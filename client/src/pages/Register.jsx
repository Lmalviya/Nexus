import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import Footer from '../components/Footer';

const Register = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [organizationName, setOrganizationName] = useState('');
    const [organizationSlug, setOrganizationSlug] = useState('');
    const [error, setError] = useState('');

    // Auto-generate slug from organization name
    useEffect(() => {
        if (organizationName) {
            const slug = organizationName
                .toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/[\s_-]+/g, '-')
                .replace(/^-+|-+$/g, '');
            setOrganizationSlug(slug);
        }
    }, [organizationName]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await axios.post('http://localhost:8000/auth/register', {
                full_name: fullName,
                email,
                password,
                organization_name: organizationName,
                organization_slug: organizationSlug
            });

            if (res.data.status === 'success') {
                login(res.data.user, res.data.token);
                navigate('/chat');
            }
        } catch (err) {
            console.error("Registration Failed", err);
            setError(err.response?.data?.detail || "Registration failed. Please try again.");
        }
    };

    return (
        <div className="flex flex-col min-h-screen bg-gray-900">
            <Header />
            <div className="flex-grow flex items-center justify-center py-8">
                <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md">
                    <h2 className="text-3xl font-bold text-white mb-6 text-center">Create Account</h2>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-2 rounded mb-4 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-gray-300 mb-1">Full Name</label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                required
                            />
                        </div>
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

                        <div className="border-t border-gray-700 pt-4 mt-4">
                            <h3 className="text-lg font-semibold text-white mb-3">Organization Details</h3>

                            <div>
                                <label className="block text-gray-300 mb-1">Organization Name</label>
                                <input
                                    type="text"
                                    value={organizationName}
                                    onChange={(e) => setOrganizationName(e.target.value)}
                                    className="w-full bg-gray-700 text-white rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g., Acme Corporation"
                                    required
                                />
                            </div>

                            <div className="mt-4">
                                <label className="block text-gray-300 mb-1">Organization Slug</label>
                                <div className="flex">
                                    <span className="bg-gray-600 text-gray-300 px-3 py-2 rounded-l flex items-center text-sm">
                                        nexus.com/
                                    </span>
                                    <input
                                        type="text"
                                        value={organizationSlug}
                                        onChange={(e) => setOrganizationSlug(e.target.value)}
                                        className="w-full bg-gray-700 text-white rounded-r px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="acme-corp"
                                        required
                                    />
                                </div>
                                <p className="text-gray-500 text-xs mt-1">This will be your organization's unique identifier</p>
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded mt-4 transition-colors"
                        >
                            Create Account & Organization
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-gray-400 text-sm">
                            Already have an account?{' '}
                            <Link to="/login" className="text-blue-400 hover:text-blue-300">
                                Sign In here
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default Register;
