'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/store/useStore';
import { authApi } from '@/services/api';
import { Loader2 } from 'lucide-react';

export default function Login() {
    const router = useRouter();
    const { setUser, setToken, hasHydrated, token } = useStore();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [error, setError] = useState('');
    const [backendStatus, setBackendStatus] = useState<'checking' | 'up' | 'down'>('checking');

    useEffect(() => {
        setMounted(true);
        if (hasHydrated && token) {
            router.push('/');
        }

        // Ping backend
        const healthUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '/health');
        fetch(healthUrl)
            .then(res => res.ok ? setBackendStatus('up') : setBackendStatus('down'))
            .catch(() => setBackendStatus('down'));
    }, [hasHydrated, token, router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const params = new URLSearchParams();
            params.append('username', email); // FastAPI uses username field
            params.append('password', password);

            const response = await authApi.login(params);
            setToken(response.data.access_token);
            setUser(response.data.user);

            router.push('/');
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.';
            const axiosError = err as { response?: { data?: { detail?: string } } };
            setError(axiosError.response?.data?.detail || errorMessage);
        } finally {
            setLoading(false);
        }
    };

    if (!mounted || !hasHydrated) return null;

    return (
        <main className="min-h-screen bg-white flex flex-col p-6 items-center justify-center">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-black text-instacart-green italic tracking-tighter mb-2">StudyPulse</h1>
                    <p className="text-instacart-grey font-semibold">Welcome back! Please login to your account.</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-bold text-instacart-dark mb-1 ml-1">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-4 rounded-xl border border-instacart-border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all"
                            placeholder="Enter your email"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-instacart-dark mb-1 ml-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-4 rounded-xl border border-instacart-border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all"
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    {error && <p className="text-red-500 text-sm py-1 ml-1 font-semibold">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-4 bg-instacart-green text-white rounded-xl font-bold text-lg shadow-lg hover:bg-instacart-green-dark active:scale-95 transition-all flex items-center justify-center"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : 'Login'}
                    </button>
                </form>

                <div className="text-center pt-8 border-t border-instacart-border mt-8">
                    <div className="flex items-center justify-center space-x-2">
                        <div className={`h-2 w-2 rounded-full ${backendStatus === 'up' ? 'bg-green-500' : backendStatus === 'down' ? 'bg-red-500' : 'bg-gray-300 animate-pulse'}`}></div>
                        <span className="text-[10px] uppercase font-bold text-instacart-grey tracking-widest">
                            API: {backendStatus === 'up' ? 'Connected' : backendStatus === 'down' ? 'Disconnected' : 'Checking...'}
                        </span>
                    </div>
                </div>
            </div>
        </main>
    );
}
