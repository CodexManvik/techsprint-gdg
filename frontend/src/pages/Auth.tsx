import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

export const Auth = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            if (isLogin) {
                // Login
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);

                const response = await api.post('/auth/login', formData);
                login(response.data.access_token);
                navigate('/dashboard');
            } else {
                // Register
                await api.post('/auth/register', {
                    email,
                    password,
                    full_name: fullName
                });
                // Auto login after register
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);
                const loginRes = await api.post('/auth/login', formData);
                login(loginRes.data.access_token);
                navigate('/dashboard');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed');
        }
    };

    return (
        <div className="min-h-screen w-full bg-black/[0.96] antialiased bg-grid-white/[0.02] relative overflow-hidden flex items-center justify-center">
            {/* Background Ambience */}
            <div className="absolute pointer-events-none inset-0 flex items-center justify-center bg-black [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>

            {/* Spotlight Effect (simplified CSS/SVG for now) */}
            <div className="absolute top-0 left-0 md:left-60 md:-top-20 opacity-50">
                <div className="w-[40rem] h-[40rem] bg-purple-500/20 rounded-full blur-[100px]" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 w-full max-w-md p-8 rounded-2xl bg-black border border-white/[0.1] shadow-[0_0_50px_-12px_rgba(255,255,255,0.1)]"
            >
                <h2 className="text-3xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400 mb-8">
                    {isLogin ? 'Welcome Back' : 'Create Account'}
                </h2>

                {error && (
                    <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-500/20 text-red-500 text-sm text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {!isLogin && (
                        <div>
                            <label className="block text-sm font-medium text-neutral-300 mb-2">Full Name</label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-neutral-900 border border-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                placeholder="John Doe"
                                required
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-neutral-300 mb-2">Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-neutral-900 border border-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-neutral-300 mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-neutral-900 border border-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full py-3 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(124,58,237,0.3)]"
                    >
                        {isLogin ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-neutral-400 text-sm">
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-purple-400 hover:text-purple-300 font-medium transition-colors"
                        >
                            {isLogin ? 'Sign Up' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </motion.div>
        </div>
    );
};
