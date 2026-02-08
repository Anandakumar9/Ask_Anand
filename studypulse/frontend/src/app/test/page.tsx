'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, Clock, Bookmark, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { testApi } from '@/services/api';

function MockTestContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const topicId = searchParams.get('topicId');
    const sessionId = searchParams.get('sessionId');

    const [questions, setQuestions] = useState<any[]>([]);
    const [currentIdx, setCurrentIdx] = useState(0);
    const [answers, setAnswers] = useState<any>({});
    const [loading, setLoading] = useState(true);
    const [testId, setTestId] = useState<number | null>(null);
    const [timeTaken, setTimeTaken] = useState(0);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const startTest = async () => {
            if (!topicId) {
                router.push('/');
                return;
            }
            try {
                const response = await testApi.startTest({
                    topic_id: parseInt(topicId),
                    session_id: sessionId ? parseInt(sessionId) : undefined,
                    question_count: 5 // Smaller count for testing
                });
                setQuestions(response.data.questions);
                setTestId(response.data.test_id);
            } catch (err) {
                console.error('Failed to start test', err);
                router.push('/');
            } finally {
                setLoading(false);
            }
        };
        startTest();
    }, [topicId, sessionId, router]);

    useEffect(() => {
        let interval: any = null;
        if (!loading && questions.length > 0) {
            interval = setInterval(() => {
                setTimeTaken(prev => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [loading, questions]);

    const handleSelect = (optionId: string) => {
        const questionId = questions[currentIdx].id;
        setAnswers({
            ...answers,
            [questionId]: optionId
        });
    };

    const handleSubmit = async () => {
        if (!testId || submitting) return;
        setSubmitting(true);

        try {
            const responses = questions.map(q => ({
                question_id: q.id,
                answer: answers[q.id] || null,
                time_spent_seconds: 0 // Could refine this to track per-question time
            }));

            const result = await testApi.submitTest(testId, responses, timeTaken);
            router.push(`/results?testId=${testId}`);
        } catch (err) {
            console.error('Failed to submit test', err);
        } finally {
            setSubmitting(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    if (questions.length === 0) return null;

    const currentQuestion = questions[currentIdx];
    const selectedOption = answers[currentQuestion.id];

    return (
        <main className="min-h-screen bg-instacart-grey-light flex flex-col">
            <header className="p-4 bg-white border-b border-instacart-border flex items-center shadow-sm">
                <button onClick={() => router.back()} className="p-1">
                    <ChevronLeft className="text-instacart-dark" />
                </button>
                <div className="flex-1 text-center">
                    <h1 className="font-bold text-instacart-dark">Question {currentIdx + 1} of {questions.length}</h1>
                </div>
                <div className="flex items-center space-x-1 bg-instacart-grey-light px-3 py-1.5 rounded-full text-instacart-dark font-mono text-sm font-bold border border-instacart-border">
                    <Clock size={16} />
                    <span>{formatTime(timeTaken)}</span>
                </div>
            </header>

            <div className="bg-instacart-border h-1.5 w-full">
                <div
                    className="bg-instacart-green h-full transition-all duration-500"
                    style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
                ></div>
            </div>

            <div className="p-4 space-y-6 flex-1 overflow-y-auto">
                <div className="card shadow-md relative">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] uppercase font-black tracking-widest bg-instacart-green text-white px-2 py-1 rounded">
                            {currentQuestion.source === 'AI' ? 'AI Question' : 'Previous Year'}
                        </span>
                        <button className="text-instacart-grey hover:text-instacart-green transition-colors">
                            <Bookmark size={20} />
                        </button>
                    </div>
                    <h2 className="text-lg font-bold text-instacart-dark leading-snug">
                        {currentQuestion.question_text}
                    </h2>
                </div>

                <div className="space-y-3">
                    {Object.entries(currentQuestion.options).map(([id, text]: any) => (
                        <div
                            key={id}
                            onClick={() => handleSelect(id)}
                            className={`flex items-center p-4 rounded-xl border-2 transition-all cursor-pointer bg-white shadow-sm ${selectedOption === id
                                    ? 'border-instacart-green bg-instacart-green-light ring-1 ring-instacart-green'
                                    : 'border-instacart-border hover:border-instacart-green'
                                }`}
                        >
                            <div className={`h-6 w-6 rounded-full border-2 flex items-center justify-center mr-4 transition-all ${selectedOption === id ? 'border-instacart-green bg-instacart-green text-white' : 'border-instacart-border'
                                }`}>
                                {selectedOption === id ? id : <span className="text-xs font-bold text-instacart-grey">{id}</span>}
                            </div>
                            <span className="font-semibold text-instacart-dark">
                                {text}
                            </span>
                            {selectedOption === id && (
                                <div className="ml-auto text-instacart-green">
                                    <CheckCircle2 size={18} fill="white" />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <div className="p-4 bg-white border-t border-instacart-border shadow-[0_-4px_10px_rgba(0,0,0,0.05)] sticky bottom-0">
                <div className="flex items-center space-x-4">
                    <button
                        disabled={currentIdx === 0}
                        onClick={() => setCurrentIdx(prev => prev - 1)}
                        className="px-6 py-4 card border-instacart-border text-instacart-dark font-bold active:scale-95 transition-all disabled:opacity-30"
                    >
                        Previous
                    </button>

                    {currentIdx === questions.length - 1 ? (
                        <button
                            onClick={handleSubmit}
                            disabled={submitting}
                            className="flex-1 py-4 bg-instacart-green text-white rounded-xl font-bold text-lg shadow-lg hover:bg-instacart-green-dark active:scale-95 transition-all flex items-center justify-center"
                        >
                            {submitting ? <Loader2 className="animate-spin text-white" /> : 'Submit Test'}
                        </button>
                    ) : (
                        <button
                            onClick={() => setCurrentIdx(prev => prev + 1)}
                            className="flex-1 py-4 bg-instacart-green text-white rounded-xl font-bold text-lg shadow-lg hover:bg-instacart-green-dark active:scale-95 transition-all"
                        >
                            Next
                        </button>
                    )}
                </div>
            </div>
        </main>
    );
}

export default function MockTest() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <MockTestContent />
        </Suspense>
    );
}
