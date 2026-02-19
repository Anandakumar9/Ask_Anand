'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, ChevronRight, Clock, BarChart2, Play, Loader2, X, Timer } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { examApi } from '@/services/api';

const DIFFICULTY_COLORS: Record<string, string> = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
};

// Timer options: 5 min (test) to 120 min (2 hours), step 5 min
const TIMER_OPTIONS = [5, 10, 15, 20, 25, 30, 45, 60, 90, 120];

function TimerSheet({ topic, onConfirm, onClose }: { topic: any; onConfirm: (mins: number) => void; onClose: () => void }) {
    const [selected, setSelected] = useState(45);

    return (
        <div className="fixed inset-0 z-50 flex items-end" onClick={onClose}>
            <div
                className="w-full bg-white rounded-t-3xl shadow-2xl p-6 pb-10"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-1">
                    <h2 className="font-bold text-lg text-instacart-dark">Set Study Timer</h2>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-instacart-grey-light transition-colors">
                        <X size={20} className="text-instacart-grey" />
                    </button>
                </div>
                <p className="text-xs text-instacart-grey mb-5">
                    <span className="font-semibold text-instacart-dark">{topic.name}</span>
                    {' '}— Questions will generate during your session.
                </p>

                <div className="grid grid-cols-5 gap-2 mb-6">
                    {TIMER_OPTIONS.map((mins) => {
                        const label = mins < 60 ? `${mins}m` : `${mins / 60}h`;
                        const isTest = mins === 5;
                        return (
                            <button
                                key={mins}
                                onClick={() => setSelected(mins)}
                                className={`py-2.5 rounded-xl text-sm font-bold border transition-all ${
                                    selected === mins
                                        ? 'bg-instacart-green text-white border-instacart-green shadow-md scale-105'
                                        : 'bg-white text-instacart-dark border-instacart-border hover:border-instacart-green'
                                }`}
                            >
                                {label}
                                {isTest && (
                                    <span className="block text-[9px] font-medium opacity-70">test</span>
                                )}
                            </button>
                        );
                    })}
                </div>

                <div className="flex items-center space-x-3 bg-instacart-green-light rounded-2xl px-4 py-3 mb-5">
                    <Timer size={18} className="text-instacart-green flex-shrink-0" />
                    <p className="text-xs text-instacart-dark font-medium">
                        {selected < 60
                            ? `${selected} minute session`
                            : selected === 60 ? '1 hour session' : `${selected / 60} hour session`}
                        {' '}— questions ready when timer ends.
                    </p>
                </div>

                <button
                    onClick={() => onConfirm(selected)}
                    className="w-full bg-instacart-green text-white font-bold py-4 rounded-2xl text-base active:scale-95 transition-all shadow-md"
                >
                    Start Studying
                </button>
            </div>
        </div>
    );
}

function TopicsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const examId = searchParams.get('examId');
    const subjectId = searchParams.get('subjectId');
    const subjectName = searchParams.get('subjectName') || 'Topics';

    const [topics, setTopics] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTopic, setSelectedTopic] = useState<any | null>(null);

    useEffect(() => {
        if (!examId || !subjectId) {
            router.push('/setup');
            return;
        }

        const fetchTopics = async () => {
            try {
                const response = await examApi.getTopics(parseInt(examId), parseInt(subjectId));
                setTopics(response.data);
            } catch (err) {
                console.error('Failed to fetch topics', err);
                router.push('/setup');
            } finally {
                setLoading(false);
            }
        };

        fetchTopics();
    }, [examId, subjectId, router]);

    const handleStartSession = (durationMins: number) => {
        if (!selectedTopic) return;
        setSelectedTopic(null);
        router.push(`/study?topicId=${selectedTopic.id}&duration=${durationMins}`);
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <>
            <main className="min-h-screen bg-instacart-grey-light pb-8">
                <header className="p-4 border-b border-instacart-border flex items-center bg-white sticky top-0 z-10">
                    <button onClick={() => router.back()} className="p-2 hover:bg-instacart-grey-light rounded-full transition-colors">
                        <ChevronLeft className="text-instacart-dark" />
                    </button>
                    <div className="flex-1 text-center">
                        <h1 className="font-bold text-lg text-instacart-dark">{decodeURIComponent(subjectName)}</h1>
                        <p className="text-xs text-instacart-grey">Select a topic to start studying</p>
                    </div>
                    <div className="w-10" />
                </header>

                <div className="p-4 space-y-3">
                    {topics.length === 0 ? (
                        <div className="text-center py-20 text-instacart-grey italic text-sm">
                            No topics found for this subject.
                        </div>
                    ) : (
                        topics.map((topic) => (
                            <div
                                key={topic.id}
                                onClick={() => setSelectedTopic(topic)}
                                className="bg-white rounded-2xl border border-instacart-border p-4 cursor-pointer hover:border-instacart-green transition-all shadow-sm"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0 mr-3">
                                        <h3 className="font-bold text-instacart-dark leading-tight">{topic.name}</h3>
                                        {topic.description && (
                                            <p className="text-xs text-instacart-grey mt-1 line-clamp-2">{topic.description}</p>
                                        )}
                                        <div className="flex items-center space-x-2 mt-2">
                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${DIFFICULTY_COLORS[topic.difficulty_level] || 'bg-gray-100 text-gray-600'}`}>
                                                {topic.difficulty_level}
                                            </span>
                                            <span className="flex items-center text-[10px] text-instacart-grey font-semibold">
                                                <Clock size={10} className="mr-1" />
                                                {topic.estimated_study_mins} mins
                                            </span>
                                            <span className="flex items-center text-[10px] text-instacart-grey font-semibold">
                                                <BarChart2 size={10} className="mr-1" />
                                                {topic.question_count} Qs
                                            </span>
                                        </div>
                                    </div>
                                    <div className="bg-instacart-green-light p-2.5 rounded-full text-instacart-green flex-shrink-0">
                                        <Play size={16} fill="currentColor" />
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </main>

            {selectedTopic && (
                <TimerSheet
                    topic={selectedTopic}
                    onConfirm={handleStartSession}
                    onClose={() => setSelectedTopic(null)}
                />
            )}
        </>
    );
}

export default function TopicsPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <TopicsContent />
        </Suspense>
    );
}
