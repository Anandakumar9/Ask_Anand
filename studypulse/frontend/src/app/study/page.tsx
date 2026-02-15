'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, MoreVertical, Pause, Square, Eye, Target, CheckCircle2, MessageSquare, Play as PlayIcon, Loader2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { studyApi } from '@/services/api';

function StudyTimerContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const topicId = searchParams.get('topicId');

    const [timeLeft, setTimeLeft] = useState(45 * 60); // Default 45 mins
    const [isActive, setIsActive] = useState(false);
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const startSession = async () => {
            if (!topicId) {
                router.push('/');
                return;
            }
            try {
                const response = await studyApi.startSession(parseInt(topicId), 45);
                setSessionId(response.data.id);
                setIsActive(true);
            } catch (err) {
                console.error('Failed to start session', err);
            } finally {
                setLoading(false);
            }
        };
        startSession();
    }, [topicId, router]);

    useEffect(() => {
        let interval: ReturnType<typeof setInterval> | null = null;
        if (isActive && timeLeft > 0) {
            interval = setInterval(() => {
                setTimeLeft((time) => time - 1);
            }, 1000);
        } else {
            clearInterval(interval);
        }
        return () => clearInterval(interval);
    }, [isActive, timeLeft]);

    const handleEndSession = async () => {
        if (sessionId) {
            try {
                const actualMins = Math.floor((45 * 60 - timeLeft) / 60);
                await studyApi.completeSession(sessionId, Math.max(1, actualMins));
                // Redirect to mock test for this topic
                router.push(`/test?topicId=${topicId}&sessionId=${sessionId}`);
            } catch (err) {
                console.error('Failed to complete session', err);
                router.push('/');
            }
        } else {
            router.push('/');
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const progress = ((45 * 60 - timeLeft) / (45 * 60)) * 100;

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <main className="min-h-screen bg-instacart-grey-light pb-8">
            <header className="p-4 flex items-center bg-white sticky top-0 z-10 border-b border-instacart-border">
                <button onClick={() => router.back()} className="p-2 hover:bg-instacart-grey-light rounded-full transition-colors">
                    <ChevronLeft className="text-instacart-dark" />
                </button>
                <h1 className="flex-1 text-center font-bold text-lg text-instacart-dark">Study Session</h1>
                <button className="p-2 hover:bg-instacart-grey-light rounded-full transition-colors">
                    <MoreVertical className="text-instacart-dark" />
                </button>
            </header>

            <div className="p-4 space-y-8 mt-4">
                <div className="flex justify-center">
                    <div className="inline-flex items-center space-x-2 bg-white px-4 py-2 rounded-full shadow-sm border border-instacart-border">
                        <span className="text-xs font-bold text-instacart-green bg-instacart-green-light px-2 py-0.5 rounded uppercase">STUDYING</span>
                        <span className="text-xs text-instacart-grey">/</span>
                        <span className="text-xs font-semibold text-instacart-dark">Topic ID: {topicId}</span>
                    </div>
                </div>

                <div className="flex justify-center py-10">
                    <div className="relative h-64 w-64 flex items-center justify-center">
                        <svg className="absolute h-full w-full -rotate-90">
                            <circle
                                cx="128"
                                cy="128"
                                r="120"
                                stroke="white"
                                strokeWidth="12"
                                fill="transparent"
                            />
                            <circle
                                cx="128"
                                cy="128"
                                r="120"
                                stroke="#43B02A"
                                strokeWidth="12"
                                fill="transparent"
                                strokeDasharray={2 * Math.PI * 120}
                                strokeDashoffset={2 * Math.PI * 120 * (1 - progress / 100)}
                                strokeLinecap="round"
                                className="transition-all duration-1000 ease-linear"
                            />
                        </svg>

                        <div className="text-center z-10">
                            <span className="block text-6xl font-black text-instacart-dark tracking-tighter">
                                {formatTime(timeLeft)}
                            </span>
                            <span className="text-instacart-grey font-bold uppercase text-xs tracking-widest mt-2 block">
                                minutes remaining
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex justify-center items-center space-x-6">
                    <button
                        onClick={() => setIsActive(!isActive)}
                        className="h-16 w-16 bg-white border border-instacart-border rounded-full flex items-center justify-center shadow-md active:scale-95 transition-all text-instacart-dark"
                    >
                        {isActive ? <Pause size={28} fill="currentColor" /> : <PlayIcon size={28} className="ml-1" fill="currentColor" />}
                    </button>

                    <button
                        onClick={handleEndSession}
                        className="h-14 w-14 bg-red-50 border border-red-100 rounded-full flex items-center justify-center shadow-sm active:scale-95 transition-all text-red-500"
                    >
                        <Square size={20} fill="currentColor" />
                    </button>

                    <button className="h-14 w-14 bg-instacart-green-light border border-instacart-green/20 rounded-full flex items-center justify-center shadow-sm active:scale-95 transition-all text-instacart-green">
                        <Eye size={24} />
                    </button>
                </div>

                <section className="mt-8">
                    <div className="card space-y-4 shadow-md border-t-4 border-t-instacart-green">
                        <div className="flex items-center space-x-3">
                            <div className="bg-instacart-green-light p-2 rounded-lg text-instacart-green">
                                <Target size={20} />
                            </div>
                            <div>
                                <h3 className="font-bold text-instacart-dark">Session Goal</h3>
                                <p className="text-xs text-instacart-grey">Complete your study and take the test!</p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-2 text-instacart-green text-sm font-semibold">
                            <CheckCircle2 size={16} />
                            <span>Session will end with a Mock Test.</span>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    );
}

export default function StudyTimer() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <StudyTimerContent />
        </Suspense>
    );
}
