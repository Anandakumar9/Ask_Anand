'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { testApi } from '@/services/api';
import { useThemeStore } from '@/store/themeStore';

interface Question {
    id: number;
    question_text: string;
    options: Record<string, string>;
    difficulty: string;
    source: string;
}

interface QuestionResult {
    question_id: number;
    question_text: string;
    options: Record<string, string>;
    user_answer: string | null;
    correct_answer: string;
    is_correct: boolean;
    explanation?: string;
    source: string;
}

function TestContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const topicId = searchParams.get('topicId');
    const sessionId = searchParams.get('sessionId');
    const { isDarkMode } = useThemeStore();

    const [phase, setPhase] = useState<'loading' | 'active' | 'submitting' | 'results'>('loading');
    const [testId, setTestId] = useState<number | null>(null);
    const [questions, setQuestions] = useState<Question[]>([]);
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [results, setResults] = useState<any | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [startTime] = useState(Date.now());

    useEffect(() => {
        if (!topicId) { router.push('/'); return; }

        const load = async () => {
            try {
                const res = await testApi.startTest({
                    topic_id: parseInt(topicId),
                    session_id: sessionId ? parseInt(sessionId) : undefined,
                    question_count: 10,
                });
                setTestId(res.data.test_id);
                setQuestions(res.data.questions || []);
                setPhase('active');
            } catch (err) {
                console.error(err);
                setError('Could not load test questions. Please go back and try again.');
                setPhase('results'); // show error screen
            }
        };
        load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSubmit = async () => {
        if (!testId) return;
        setPhase('submitting');
        const totalTime = Math.floor((Date.now() - startTime) / 1000);
        const responses = questions.map((q) => ({
            question_id: q.id,
            answer: answers[q.id] || null,
        }));
        try {
            const res = await testApi.submitTest(testId, responses, totalTime);
            // Persist question IDs so future sessions exclude them
            if (topicId && questions.length > 0) {
                try {
                    const key = `sp_seen_${topicId}`;
                    const existing: number[] = JSON.parse(localStorage.getItem(key) || '[]');
                    const merged = Array.from(new Set([...existing, ...questions.map((q) => q.id)]));
                    localStorage.setItem(key, JSON.stringify(merged));
                } catch {}
            }
            setResults(res.data);
            setPhase('results');
        } catch (err) {
            console.error(err);
            setError('Failed to submit test. Please try again.');
            setPhase('active');
        }
    };

    // ── Loading ──
    if (phase === 'loading') {
        return (
            <div className={`min-h-screen flex flex-col items-center justify-center gap-4 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
                <p className={`text-sm ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>Loading questions…</p>
            </div>
        );
    }

    // ── Submitting ──
    if (phase === 'submitting') {
        return (
            <div className={`min-h-screen flex flex-col items-center justify-center gap-4 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
                <p className={`text-sm ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>Submitting your answers…</p>
            </div>
        );
    }

    // ── Results ──
    if (phase === 'results') {
        if (error && !results) {
            return (
                <main className={`min-h-screen ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-instacart-grey-light'}`}>
                    <header className={`p-4 flex items-center border-b ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                        <button onClick={() => router.push('/')} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go to home">
                            <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                        </button>
                        <h1 className={`flex-1 text-center font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Mock Test</h1>
                        <div className="w-10" />
                    </header>
                    <div className="p-4">
                        <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-2xl p-4">
                            <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                        <button onClick={() => router.back()} className="w-full mt-4 bg-instacart-green text-white font-bold py-4 rounded-2xl">
                            Go Back
                        </button>
                    </div>
                </main>
            );
        }

        const score = results?.score_percentage ?? 0;
        const correct = results?.correct_count ?? 0;
        const total = results?.total_questions ?? 0;
        const starEarned = results?.star_earned ?? false;
        const questionResults: QuestionResult[] = results?.questions ?? [];

        return (
            <main className={`min-h-screen pb-10 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-instacart-grey-light'}`}>
                <header className={`p-4 flex items-center sticky top-0 z-10 border-b ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                    <button onClick={() => router.push('/')} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go to home">
                        <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                    </button>
                    <h1 className={`flex-1 text-center font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Results</h1>
                    <div className="w-10" />
                </header>

                <div className="p-4 space-y-4">
                    {/* Score card */}
                    <div className={`rounded-2xl p-5 text-center ${starEarned ? 'bg-instacart-green' : isDarkMode ? 'bg-instacart-dark-card border border-instacart-dark-border' : 'bg-white border border-instacart-border'}`}>
                        <p className={`text-5xl font-black ${starEarned ? 'text-white' : isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>
                            {score.toFixed(0)}%
                        </p>
                        <p className={`text-sm font-semibold mt-1 ${starEarned ? 'text-white/80' : isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                            {correct}/{total} correct
                            {starEarned ? ' · Star earned!' : ''}
                        </p>
                        {results?.feedback_message && (
                            <p className={`text-xs mt-2 ${starEarned ? 'text-white/70' : isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                                {results.feedback_message}
                            </p>
                        )}
                    </div>

                    {/* Per-question breakdown */}
                    <div className="space-y-3">
                        {questionResults.map((qr, idx) => (
                            <div key={qr.question_id} className={`rounded-2xl border p-4 shadow-sm ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                                <div className="flex items-start gap-2 mb-2">
                                    {qr.is_correct
                                        ? <CheckCircle2 size={16} className="text-instacart-green flex-shrink-0 mt-0.5" />
                                        : <XCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />}
                                    <p className={`text-sm font-semibold leading-snug ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>
                                        <span className="text-instacart-green font-black mr-1">Q{idx + 1}.</span>
                                        {qr.question_text}
                                    </p>
                                </div>
                                <div className="space-y-1.5 mt-2">
                                    {Object.entries(qr.options).map(([key, val]) => {
                                        const isCorrect = key === qr.correct_answer;
                                        const isUser = key === qr.user_answer;
                                        const isWrong = isUser && !qr.is_correct;
                                        return (
                                            <div
                                                key={key}
                                                className={`flex items-start gap-2 px-3 py-2 rounded-xl text-sm border ${
                                                    isCorrect
                                                        ? 'border-instacart-green bg-instacart-green-light font-semibold'
                                                        : isWrong
                                                        ? 'border-red-300 bg-red-50 text-red-700'
                                                        : isDarkMode
                                                            ? 'border-instacart-dark-border text-instacart-dark-text-secondary'
                                                            : 'border-instacart-border text-instacart-grey'
                                                }`}
                                            >
                                                <span className={`font-bold flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${
                                                    isCorrect ? 'bg-instacart-green text-white'
                                                    : isWrong ? 'bg-red-400 text-white'
                                                    : isDarkMode
                                                        ? 'bg-instacart-dark-border text-instacart-dark-text-secondary'
                                                        : 'bg-instacart-grey-light text-instacart-grey'
                                                }`}>{key}</span>
                                                <span className="leading-snug">{val}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={() => router.push('/')}
                        className="w-full bg-instacart-green text-white font-bold py-4 rounded-2xl text-base active:scale-95 transition-all"
                    >
                        Back to Home
                    </button>
                </div>
            </main>
        );
    }

    // ── Active test ──
    const answered = Object.keys(answers).length;
    return (
        <main className={`min-h-screen pb-24 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-instacart-grey-light'}`}>
            <header className={`p-4 flex items-center sticky top-0 z-10 border-b ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                <button onClick={() => router.back()} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go back">
                    <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                </button>
                <h1 className={`flex-1 text-center font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Mock Test</h1>
                <span className={`text-xs font-bold mr-2 ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>{answered}/{questions.length}</span>
            </header>

            <div className="p-4 space-y-4">
                {questions.map((q, idx) => (
                    <div key={q.id} className={`rounded-2xl border p-4 shadow-sm ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                        <div className="flex items-start gap-2 mb-3">
                            <span className="text-xs font-black text-instacart-green bg-instacart-green-light px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5">
                                Q{idx + 1}
                            </span>
                            <p className={`text-sm font-semibold leading-snug ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{q.question_text}</p>
                        </div>
                        <div className="space-y-2">
                            {Object.entries(q.options).map(([key, val]) => {
                                const picked = answers[q.id] === key;
                                return (
                                    <button
                                        key={key}
                                        onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: key }))}
                                        className={`w-full text-left flex items-start gap-3 px-3 py-2.5 rounded-xl border text-sm transition-all ${
                                            picked
                                                ? 'border-instacart-green bg-instacart-green-light font-semibold text-instacart-dark'
                                                : isDarkMode
                                                    ? 'border-instacart-dark-border hover:border-instacart-green text-instacart-dark-text'
                                                    : 'border-instacart-border hover:border-instacart-green text-instacart-dark'
                                        }`}
                                    >
                                        <span className={`font-bold flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${picked ? 'bg-instacart-green text-white' : isDarkMode ? 'bg-instacart-dark-border text-instacart-dark-text-secondary' : 'bg-instacart-grey-light text-instacart-grey'}`}>
                                            {key}
                                        </span>
                                        <span className="leading-snug">{val}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            {/* Sticky submit bar */}
            <div className={`fixed bottom-0 left-0 right-0 p-4 border-t shadow-lg ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                {error && <p className="text-xs text-red-500 mb-2 text-center">{error}</p>}
                <button
                    onClick={handleSubmit}
                    disabled={answered === 0}
                    className="w-full bg-instacart-green text-white font-bold py-4 rounded-2xl text-base active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Submit Test ({answered}/{questions.length} answered)
                </button>
            </div>
        </main>
    );
}

export default function TestPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <TestContent />
        </Suspense>
    );
}
