'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { ChevronLeft, Pause, Square, Target, Play as PlayIcon, Loader2, BookOpen } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { studyApi } from '@/services/api';
import { useThemeStore } from '@/store/themeStore';

function StudyTimerContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const topicId = searchParams.get('topicId');
    const durationParam = searchParams.get('duration');
    const totalMins = durationParam ? Math.max(5, Math.min(120, parseInt(durationParam))) : 45;
    const { isDarkMode } = useThemeStore();

    const [timeLeft, setTimeLeft] = useState(totalMins * 60);
    const [isActive, setIsActive] = useState(false);
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [ending, setEnding] = useState(false);
    const [sessionReady, setSessionReady] = useState(false);

    // Persist previously seen question IDs per topic in localStorage
    const getPreviousQuestionIds = useCallback((): number[] => {
        if (typeof window === 'undefined' || !topicId) return [];
        try {
            const raw = localStorage.getItem(`sp_seen_${topicId}`);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }, [topicId]);

    useEffect(() => {
        const startSession = async () => {
            if (!topicId) { router.push('/'); return; }
            try {
                const previousIds = getPreviousQuestionIds();
                const response = await studyApi.startSession(
                    parseInt(topicId),
                    totalMins,
                    previousIds,
                );
                setSessionId(response.data.session_id);
                setIsActive(true);
            } catch (err) {
                console.error('Failed to start session', err);
            } finally {
                setLoading(false);
            }
        };
        startSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Countdown tick
    useEffect(() => {
        if (!isActive || timeLeft <= 0) return;
        const interval = setInterval(() => setTimeLeft((t) => t - 1), 1000);
        return () => clearInterval(interval);
    }, [isActive, timeLeft]);

    // Auto-end when timer hits 0
    useEffect(() => {
        if (timeLeft === 0 && isActive && sessionId) {
            handleEndSession();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [timeLeft]);

    const handleEndSession = async () => {
        if (!sessionId || ending) return;
        setIsActive(false);
        setEnding(true);
        const actualMins = Math.max(1, Math.floor((totalMins * 60 - timeLeft) / 60));
        try {
            await studyApi.completeSession(sessionId, actualMins);
        } catch (err) {
            console.error('Failed to complete session', err);
        }
        setEnding(false);
        setSessionReady(true);
    };

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const progress = ((totalMins * 60 - timeLeft) / (totalMins * 60)) * 100;

    // ── Loading / starting session ──
    if (loading) {
        return (
            <div className={`min-h-screen flex flex-col items-center justify-center gap-4 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
                <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-instacart-grey'}`}>Starting session & generating questions…</p>
            </div>
        );
    }

    // ── Completing session (saving to backend) ──
    if (ending) {
        return (
            <div className={`min-h-screen flex flex-col items-center justify-center gap-4 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
                <p className={`font-bold text-base ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>Wrapping up session…</p>
            </div>
        );
    }

    // ── Session complete — show Start Test button ──
    if (sessionReady) {
        return (
            <main className={`min-h-screen flex flex-col items-center justify-center p-6 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
                <div className="w-full max-w-sm space-y-6 text-center">
                    <div className="text-6xl">🎉</div>
                    <div>
                        <h2 className={`text-2xl font-black mb-2 ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>Session Complete!</h2>
                        <p className={`font-medium ${isDarkMode ? 'text-gray-400' : 'text-instacart-grey'}`}>
                            Your questions are ready. Start the test whenever you&apos;re set.
                        </p>
                    </div>
                    <div className={`rounded-2xl p-4 border ${isDarkMode ? 'bg-green-900/30 border-green-800' : 'bg-instacart-green-light border-instacart-green border-opacity-30'}`}>
                        <p className={`font-bold text-sm ${isDarkMode ? 'text-green-400' : 'text-instacart-green'}`}>
                            10 questions generated based on your study session
                        </p>
                    </div>
                    <button
                        onClick={() => router.push(`/test?topicId=${topicId}&sessionId=${sessionId}`)}
                        className="w-full py-5 bg-instacart-green text-white rounded-2xl font-black text-xl shadow-lg active:scale-95 transition-all"
                    >
                        Start Test
                    </button>
                    <button
                        onClick={() => router.push('/')}
                        className={`text-sm font-semibold hover:underline ${isDarkMode ? 'text-gray-400' : 'text-instacart-grey'}`}
                    >
                        Skip for now
                    </button>
                </div>
            </main>
        );
    }

    // ── Active timer ──
    const durationLabel = totalMins < 60 ? `${totalMins} min` : totalMins === 60 ? '1 hr' : `${totalMins / 60} hr`;

    return (
        <main className={`min-h-screen pb-8 ${isDarkMode ? 'bg-gray-900' : 'bg-instacart-grey-light'}`}>
            <header className={`p-4 flex items-center sticky top-0 z-10 border-b ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-instacart-border'}`}>
                <button onClick={() => router.back()} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-instacart-grey-light'}`}>
                    <ChevronLeft className={isDarkMode ? 'text-white' : 'text-instacart-dark'} />
                </button>
                <h1 className={`flex-1 text-center font-bold text-lg ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>Study Session</h1>
                <div className="w-10" />
            </header>

            <div className="p-4 space-y-8 mt-4">
                <div className="flex justify-center">
                    <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-instacart-border'}`}>
                        <span className="text-xs font-bold text-instacart-green bg-instacart-green-light px-2 py-0.5 rounded uppercase">
                            {isActive ? 'STUDYING' : 'PAUSED'}
                        </span>
                        <span className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-instacart-grey'}`}>/</span>
                        <span className={`text-xs font-semibold ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>{durationLabel} session</span>
                    </div>
                </div>

                {/* Circular timer */}
                <div className="flex justify-center py-10">
                    <div className="relative h-64 w-64 flex items-center justify-center">
                        <svg className="absolute h-full w-full -rotate-90">
                            <circle cx="128" cy="128" r="120" stroke={isDarkMode ? '#374151' : 'white'} strokeWidth="12" fill="transparent" />
                            <circle
                                cx="128" cy="128" r="120"
                                stroke="#43B02A" strokeWidth="12" fill="transparent"
                                strokeDasharray={2 * Math.PI * 120}
                                strokeDashoffset={2 * Math.PI * 120 * (1 - progress / 100)}
                                strokeLinecap="round"
                                className="transition-all duration-1000 ease-linear"
                            />
                        </svg>
                        <div className="text-center z-10">
                            <span className={`block text-6xl font-black tracking-tighter ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>
                                {formatTime(timeLeft)}
                            </span>
                            <span className={`font-bold uppercase text-xs tracking-widest mt-2 block ${isDarkMode ? 'text-gray-400' : 'text-instacart-grey'}`}>
                                remaining
                            </span>
                        </div>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex justify-center items-center space-x-6">
                    <button
                        onClick={() => setIsActive(!isActive)}
                        className={`h-16 w-16 border rounded-full flex items-center justify-center shadow-md active:scale-95 transition-all ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-instacart-border text-instacart-dark'}`}
                    >
                        {isActive
                            ? <Pause size={28} fill="currentColor" />
                            : <PlayIcon size={28} className="ml-1" fill="currentColor" />}
                    </button>

                    <button
                        onClick={handleEndSession}
                        className={`h-14 w-14 border rounded-full flex items-center justify-center shadow-sm active:scale-95 transition-all ${isDarkMode ? 'bg-red-900/30 border-red-800 text-red-400' : 'bg-red-50 border-red-100 text-red-500'}`}
                    >
                        <Square size={20} fill="currentColor" />
                    </button>
                </div>

                {/* Info card */}
                <section>
                    <div className={`space-y-4 shadow-md border-t-4 border-t-instacart-green rounded-2xl p-4 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
                        <div className="flex items-center space-x-3">
                            <div className="bg-instacart-green-light p-2 rounded-lg text-instacart-green">
                                <Target size={20} />
                            </div>
                            <div>
                                <h3 className={`font-bold ${isDarkMode ? 'text-white' : 'text-instacart-dark'}`}>Session Goal</h3>
                                <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-instacart-grey'}`}>Questions are generating in the background.</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2 text-instacart-green text-sm font-semibold">
                            <BookOpen size={16} />
                            <span>When the timer ends you&apos;ll see a Start Test button.</span>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    );
}

export default function StudyTimer() {
    const { isDarkMode } = useThemeStore();
    
    return (
        <Suspense fallback={
            <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <StudyTimerContent />
        </Suspense>
    );
}
