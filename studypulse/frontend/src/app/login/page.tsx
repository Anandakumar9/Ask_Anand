'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/store/useStore';
import { authApi } from '@/services/api';
import { Loader2 } from 'lucide-react';
import { createClient } from '@supabase/supabase-js';
import { useThemeStore } from '@/store/themeStore';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null;

type Mode = 'login' | 'register' | 'forgot' | 'reset';

export default function Login() {
    const router = useRouter();
    const { setUser, setToken, hasHydrated, token } = useStore();
    const { isDarkMode } = useThemeStore();
    const [mode, setMode] = useState<Mode>('login');
    const [email, setEmail] = useState('');
    const [name, setName] = useState('');
    const [password, setPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [recoveryToken, setRecoveryToken] = useState('');
    const [loading, setLoading] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [backendStatus, setBackendStatus] = useState<'checking' | 'up' | 'down'>('checking');

    useEffect(() => {
        setMounted(true);

        // Ping backend
        fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'}/health`)
            .then(res => res.ok ? setBackendStatus('up') : setBackendStatus('down'))
            .catch(() => setBackendStatus('down'));

        // Check for Supabase recovery token in URL hash (forgot password redirect)
        if (typeof window !== 'undefined') {
            const hash = window.location.hash;
            if (hash.includes('type=recovery')) {
                const params = new URLSearchParams(hash.replace('#', ''));
                const t = params.get('access_token');
                if (t) {
                    setRecoveryToken(t);
                    setMode('reset');
                    window.history.replaceState(null, '', window.location.pathname);
                    return;
                }
            }
        }

        if (hasHydrated && token) {
            router.push('/');
            return;
        }

        // Handle Google OAuth redirect callback
        if (supabase) {
            const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
                if (event === 'SIGNED_IN' && session?.access_token) {
                    setGoogleLoading(true);
                    try {
                        const res = await authApi.googleAuth(session.access_token);
                        setToken(res.data.access_token);
                        setUser(res.data.user);
                        router.push('/');
                    } catch (err: any) {
                        setError(err.response?.data?.detail || 'Google sign-in failed. Please try again.');
                        setGoogleLoading(false);
                    }
                }
            });
            return () => subscription.unsubscribe();
        }
    }, [hasHydrated, token, router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);
            const response = await authApi.login(params);
            setToken(response.data.access_token);
            setUser(response.data.user);
            router.push('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await authApi.register({ email, name, password });
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);
            const response = await authApi.login(params);
            setToken(response.data.access_token);
            setUser(response.data.user);
            router.push('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleForgotPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');
        try {
            await authApi.forgotPassword(email);
            setSuccess('Check your inbox — a reset link has been sent if that email is registered.');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Could not send reset email. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            // Update password in Supabase (consumes recovery session)
            if (supabase) {
                await supabase.auth.updateUser({ password: newPassword });
            }
            // Update bcrypt hash in our DB
            await authApi.resetPassword(recoveryToken, newPassword);
            setSuccess('Password updated! Redirecting to login...');
            setTimeout(() => switchMode('login'), 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        if (!supabase) {
            setError('Google sign-in is not available. Please use email and password.');
            return;
        }
        setGoogleLoading(true);
        setError('');
        try {
            const { error: oauthError } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo: `${window.location.origin}/login` },
            });
            if (oauthError) throw oauthError;
        } catch (err: any) {
            setError(
                err.message?.includes('provider is not enabled')
                    ? 'Google sign-in is not enabled yet. Please use email and password for now.'
                    : err.message || 'Google sign-in failed. Please try again.'
            );
            setGoogleLoading(false);
        }
    };

    const switchMode = (newMode: Mode) => {
        setMode(newMode);
        setError('');
        setSuccess('');
        setEmail('');
        setPassword('');
        setName('');
        setNewPassword('');
    };

    if (!mounted || !hasHydrated) {
        return (
            <main className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <div className="text-center">
                    <Loader2 className="animate-spin text-instacart-green mx-auto mb-4" size={48} />
                    <p className="text-instacart-grey font-semibold">Loading StudyPulse...</p>
                </div>
            </main>
        );
    }

    if (googleLoading) {
        return (
            <main className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <div className="text-center">
                    <Loader2 className="animate-spin text-instacart-green mx-auto mb-4" size={48} />
                    <p className="text-instacart-grey font-semibold">Signing you in with Google...</p>
                </div>
            </main>
        );
    }

    // ── Set New Password screen (after clicking reset email link) ───────────────
    if (mode === 'reset') {
        return (
            <main className={`min-h-screen flex flex-col p-6 items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <div className="w-full max-w-md space-y-6">
                    <div className="text-center">
                        <h1 className="text-3xl font-black text-instacart-green italic tracking-tighter mb-2">StudyPulse</h1>
                        <p className="text-instacart-grey font-semibold">Set your new password.</p>
                    </div>
                    <form onSubmit={handleResetPassword} className="space-y-4">
                        <div>
                            <label className={`block text-sm font-bold mb-1 ml-1 ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>New Password</label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={e => setNewPassword(e.target.value)}
                                className={`w-full px-4 py-4 rounded-xl border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all ${
                                    isDarkMode 
                                        ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text placeholder-instacart-dark-text-secondary' 
                                        : 'bg-white border-instacart-border text-instacart-dark'
                                }`}
                                placeholder="Min 8 chars, 1 digit, 1 special char"
                                required
                            />
                        </div>
                        {error && <p className="text-red-500 text-sm py-1 ml-1 font-semibold">{error}</p>}
                        {success && <p className="text-green-600 text-sm py-1 ml-1 font-semibold">{success}</p>}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-4 bg-instacart-green text-white rounded-xl font-bold text-lg shadow-lg hover:bg-instacart-green-dark active:scale-95 transition-all flex items-center justify-center"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : 'Set New Password'}
                        </button>
                    </form>
                </div>
            </main>
        );
    }

    // ── Main login / register / forgot screens ──────────────────────────────────
    return (
        <main className={`min-h-screen flex flex-col p-6 items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
            <div className="w-full max-w-md space-y-6">
                {/* Header */}
                <div className="text-center">
                    <h1 className="text-3xl font-black text-instacart-green italic tracking-tighter mb-2">StudyPulse</h1>
                    <p className="text-instacart-grey font-semibold">
                        {mode === 'login' && 'Welcome back! Login to your account.'}
                        {mode === 'register' && 'Create a new account to get started.'}
                        {mode === 'forgot' && 'Enter your email to reset your password.'}
                    </p>
                </div>

                {/* Google Sign-In */}
                {mode !== 'forgot' && (
                    <button
                        type="button"
                        onClick={handleGoogleSignIn}
                        disabled={googleLoading}
                        className={`w-full py-3.5 border-2 rounded-xl font-bold flex items-center justify-center gap-3 hover:bg-gray-50 active:scale-95 transition-all shadow-sm ${
                            isDarkMode 
                                ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text' 
                                : 'bg-white border-instacart-border text-instacart-dark'
                        }`}
                    >
                        <svg width="20" height="20" viewBox="0 0 48 48">
                            <path fill="#EA4335" d="M24 9.5c3.2 0 5.9 1.1 8.1 2.9l6-6C34.3 3.1 29.5 1 24 1 14.8 1 6.9 6.6 3.4 14.6l7 5.4 13.8C12.1 17.6 9.5 24 9.5z"/>
                            <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 6.9-10.1 6.9-17z"/>
                            <path fill="#FBBC05" d="M10.4 28.4A14.7 14.7 0 0 1 9.5 24c0-1.5.3-3 .7-4.4l-7-5.4A23.8 23.8 0 0 0 .5 24c0 3.8.9 7.4 2.7 10.6l7.2-6.2z"/>
                            <path fill="#34A853" d="M24 47c5.5 0 10.1-1.8 13.4-4.9l-7.5-5.8c-1.8 1.2-4.2 1.9-5.9 1.9-6.3 0-11.7-4.2-13.6-9.9l-7.2 6.2C6.8 41.3 14.8 47 24 47z"/>
                        </svg>
                        Continue with Google
                    </button>
                )}

                {/* Divider */}
                {mode !== 'forgot' && (
                    <div className="flex items-center gap-3">
                        <div className={`flex-1 h-px ${isDarkMode ? 'bg-instacart-dark-border' : 'bg-instacart-border'}`} />
                        <span className="text-xs font-bold text-instacart-grey uppercase tracking-widest">or</span>
                        <div className={`flex-1 h-px ${isDarkMode ? 'bg-instacart-dark-border' : 'bg-instacart-border'}`} />
                    </div>
                )}

                {/* Form */}
                <form
                    onSubmit={mode === 'login' ? handleLogin : mode === 'register' ? handleRegister : handleForgotPassword}
                    className="space-y-4"
                >
                    {mode === 'register' && (
                        <div>
                            <label className={`block text-sm font-bold mb-1 ml-1 ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Full Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className={`w-full px-4 py-4 rounded-xl border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all ${
                                    isDarkMode 
                                        ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text placeholder-instacart-dark-text-secondary' 
                                        : 'bg-white border-instacart-border text-instacart-dark'
                                }`}
                                placeholder="Enter your full name"
                                required
                            />
                        </div>
                    )}

                    <div>
                        <label className={`block text-sm font-bold mb-1 ml-1 ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            className={`w-full px-4 py-4 rounded-xl border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all ${
                                isDarkMode 
                                    ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text placeholder-instacart-dark-text-secondary' 
                                    : 'bg-white border-instacart-border text-instacart-dark'
                            }`}
                            placeholder="Enter your email"
                            required
                        />
                    </div>

                    {mode !== 'forgot' && (
                        <div>
                            <label className={`block text-sm font-bold mb-1 ml-1 ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                className={`w-full px-4 py-4 rounded-xl border focus:ring-2 focus:ring-instacart-green focus:outline-none transition-all ${
                                    isDarkMode 
                                        ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text placeholder-instacart-dark-text-secondary' 
                                        : 'bg-white border-instacart-border text-instacart-dark'
                                }`}
                                placeholder={mode === 'register' ? 'Min 8 chars, 1 digit, 1 special char' : 'Enter your password'}
                                required
                            />
                        </div>
                    )}

                    {error && <p className="text-red-500 text-sm py-1 ml-1 font-semibold">{error}</p>}
                    {success && <p className="text-green-600 text-sm py-1 ml-1 font-semibold">{success}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-4 bg-instacart-green text-white rounded-xl font-bold text-lg shadow-lg hover:bg-instacart-green-dark active:scale-95 transition-all flex items-center justify-center"
                    >
                        {loading
                            ? <Loader2 className="animate-spin" />
                            : mode === 'login' ? 'Login'
                            : mode === 'register' ? 'Create Account'
                            : 'Send Reset Link'}
                    </button>
                </form>

                {/* Switch mode + Forgot Password — grouped cleanly below submit */}
                <div className="text-center space-y-3">
                    {mode === 'login' && (
                        <>
                            <p className="text-instacart-grey text-sm">
                                Don&apos;t have an account?{' '}
                                <button onClick={() => switchMode('register')} className="text-instacart-green font-bold hover:underline">
                                    Register
                                </button>
                            </p>
                            <p>
                                <button
                                    onClick={() => switchMode('forgot')}
                                    className="text-instacart-grey text-sm font-semibold hover:text-instacart-green hover:underline transition-colors"
                                >
                                    Forgot password?
                                </button>
                            </p>
                        </>
                    )}
                    {mode === 'register' && (
                        <>
                            <p className="text-instacart-grey text-sm">
                                Already have an account?{' '}
                                <button onClick={() => switchMode('login')} className="text-instacart-green font-bold hover:underline">
                                    Login
                                </button>
                            </p>
                            <p>
                                <button
                                    onClick={() => switchMode('forgot')}
                                    className="text-instacart-grey text-sm font-semibold hover:text-instacart-green hover:underline transition-colors"
                                >
                                    Forgot password?
                                </button>
                            </p>
                        </>
                    )}
                    {mode === 'forgot' && (
                        <button onClick={() => switchMode('login')} className="text-instacart-green font-bold text-sm hover:underline">
                            Back to Login
                        </button>
                    )}
                </div>

                {/* API status dot */}
                <div className="text-center pt-2 border-t border-instacart-border">
                    <div className="flex items-center justify-center space-x-2">
                        <div className={`h-2 w-2 rounded-full ${backendStatus === 'up' ? 'bg-green-500' : backendStatus === 'down' ? 'bg-red-500' : 'bg-gray-300 animate-pulse'}`} />
                        <span className="text-[10px] uppercase font-bold text-instacart-grey tracking-widest">
                            API: {backendStatus === 'up' ? 'Connected' : backendStatus === 'down' ? 'Disconnected' : 'Checking...'}
                        </span>
                    </div>
                </div>
            </div>
        </main>
    );
}
