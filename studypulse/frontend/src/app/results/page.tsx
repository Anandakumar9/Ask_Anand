'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, ChevronLeft, Share2, Loader2, XCircle, Clock, Star, TrendingUp, Zap } from 'lucide-react';
import { testApi } from '@/services/api';
import confetti from 'canvas-confetti';

function ResultsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const testId = searchParams.get('testId');

    const [results, setResults] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchResults = async () => {
            if (!testId) {
                router.push('/');
                return;
            }
            try {
                const response = await testApi.getResults(parseInt(testId));
                setResults(response.data);

                if (response.data.star_earned) {
                    confetti({
                        particleCount: 150,
                        spread: 70,
                        origin: { y: 0.6 },
                        colors: ['#43B02A', '#2D8A1E', '#E8F5E3', '#facc15']
                    });
                }
            } catch (err) {
                console.error('Failed to fetch results', err);
                router.push('/');
            } finally {
                setLoading(false);
            }
        };
        fetchResults();
    }, [testId, router]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    };

    return (
        <main className="min-h-screen bg-instacart-grey-light pb-24">
            <header className="p-4 bg-white border-b border-instacart-border flex items-center sticky top-0 z-10">
                <button onClick={() => router.push('/')} className="p-1">
                    <XCircle className="text-instacart-grey" />
                </button>
                <h1 className="flex-1 text-center font-bold text-instacart-dark">Test Results</h1>
                <button className="p-1">
                    <Share2 size={20} className="text-instacart-green" />
                </button>
            </header>

            <div className="p-4 space-y-6">
                <section className="text-center py-6 bg-white rounded-2xl shadow-sm border border-instacart-border">
                    {results.star_earned ? (
                        <div className="mb-4 flex flex-col items-center">
                            <div className="bg-yellow-100 p-4 rounded-full mb-3 text-yellow-500">
                                <Star size={48} fill="currentColor" />
                            </div>
                            <h2 className="text-2xl font-black text-instacart-dark">Outstanding! 🎉</h2>
                            <p className="text-instacart-green font-bold">You earned a star!</p>
                        </div>
                    ) : (
                        <div className="mb-4 flex flex-col items-center">
                            <div className="bg-instacart-green-light p-4 rounded-full mb-3 text-instacart-green">
                                <CheckCircle2 size={48} />
                            </div>
                            <h2 className="text-2xl font-black text-instacart-dark">Test Completed</h2>
                            <p className="text-instacart-grey font-semibold">Good effort! Keep practicing.</p>
                        </div>
                    )}

                    <div className="mt-6 flex flex-col items-center">
                        <span className="text-5xl font-black text-instacart-green">{Math.round(results.score_percentage)}%</span>
                        <span className="text-xs font-bold text-instacart-grey uppercase tracking-widest mt-1">Your Score</span>
                    </div>

                    <div className="mt-8 grid grid-cols-3 gap-2 px-4">
                        <div className="flex flex-col items-center p-3 bg-instacart-grey-light rounded-xl">
                            <CheckCircle2 size={18} className="text-instacart-green mb-1" />
                            <span className="font-bold text-sm text-instacart-dark">{results.correct_count}</span>
                            <span className="text-[10px] text-instacart-grey font-bold">Correct</span>
                        </div>
                        <div className="flex flex-col items-center p-3 bg-instacart-grey-light rounded-xl">
                            <XCircle size={18} className="text-red-500 mb-1" />
                            <span className="font-bold text-sm text-instacart-dark">{results.incorrect_count}</span>
                            <span className="text-[10px] text-instacart-grey font-bold">Wrong</span>
                        </div>
                        <div className="flex flex-col items-center p-3 bg-instacart-grey-light rounded-xl">
                            <Clock size={18} className="text-blue-500 mb-1" />
                            <span className="font-bold text-sm text-instacart-dark">{formatTime(results.time_taken_seconds)}</span>
                            <span className="text-[10px] text-instacart-grey font-bold">Time</span>
                        </div>
                    </div>
                </section>

                <section className="card shadow-sm space-y-4">
                    <h3 className="font-bold text-instacart-dark flex items-center">
                        <Zap size={18} className="mr-2 text-instacart-green" fill="currentColor" />
                        Performance Insights
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between text-xs font-bold mb-1.5 uppercase tracking-tighter">
                                <span className="text-instacart-grey">Accuracy</span>
                                <span className="text-instacart-green">{results.accuracy}%</span>
                            </div>
                            <div className="w-full bg-instacart-border h-2 rounded-full">
                                <div
                                    className="bg-instacart-green h-full rounded-full"
                                    style={{ width: `${results.accuracy}%` }}
                                ></div>
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between text-xs font-bold mb-1.5 uppercase tracking-tighter">
                                <span className="text-instacart-grey">Speed</span>
                                <span className="text-instacart-dark">{results.speed_rating.toUpperCase()}</span>
                            </div>
                            <div className="w-full bg-instacart-border h-2 rounded-full">
                                <div
                                    className={`h-full rounded-full ${results.speed_rating === 'fast' ? 'bg-instacart-green' : 'bg-yellow-400'}`}
                                    style={{ width: results.speed_rating === 'fast' ? '90%' : '60%' }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </section>

                <div className="space-y-3 pt-4">
                    <button className="w-full py-4 btn-secondary">
                        Analyze Answers
                    </button>
                    <button
                        onClick={() => router.push('/')}
                        className="w-full py-4 btn-primary shadow-lg shadow-instacart/20"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        </main>
    );
}

export default function Results() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <ResultsContent />
        </Suspense>
    );
}
