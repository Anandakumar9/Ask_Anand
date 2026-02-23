'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, Clock, BarChart2, Play, Loader2, X, Timer, Shuffle } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { examApi } from '@/services/api';
import { useThemeStore } from '@/store/themeStore';

const DIFFICULTY_COLORS: Record<string, string> = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
};

const TIMER_OPTIONS = [5, 10, 15, 20, 25, 30, 45, 60, 90, 120];

function TimerSheet({ topic, onConfirm, onClose, isDarkMode }: { topic: any; onConfirm: (mins: number) => void; onClose: () => void; isDarkMode: boolean }) {
    const [selected, setSelected] = useState(45);

    return (
        <div className="fixed inset-0 z-50 flex items-end" onClick={onClose}>
            <div
                className={`w-full rounded-t-3xl shadow-2xl p-6 pb-10 ${isDarkMode ? 'bg-instacart-dark-card' : 'bg-white'}`}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-1">
                    <h2 className={`font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Set Study Timer</h2>
                    <button onClick={onClose} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Close">
                        <X size={20} className={isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'} />
                    </button>
                </div>
                <p className={`text-xs mb-5 ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                    <span className={`font-semibold ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{topic.name}</span>
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
                                        : isDarkMode
                                            ? 'bg-instacart-dark-border text-instacart-dark-text border-instacart-dark-border hover:border-instacart-green'
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

                <div className={`flex items-center space-x-3 rounded-2xl px-4 py-3 mb-5 ${isDarkMode ? 'bg-instacart-green-light/20' : 'bg-instacart-green-light'}`}>
                    <Timer size={18} className="text-instacart-green flex-shrink-0" />
                    <p className={`text-xs font-medium ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>
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
    const { isDarkMode } = useThemeStore();

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

    const handleRandomTopic = () => {
        if (topics.length === 0) return;
        const randomIndex = Math.floor(Math.random() * topics.length);
        setSelectedTopic(topics[randomIndex]);
    };

    if (loading) {
        return (
            <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <>
            <main className={`min-h-screen pb-8 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-instacart-grey-light'}`}>
                <header className={`p-4 border-b sticky top-0 z-10 ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                    <div className="flex items-center">
                        <button onClick={() => router.back()} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go back">
                            <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                        </button>
                        <div className="flex-1 text-center px-2">
                            <h1 className={`font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{decodeURIComponent(subjectName)}</h1>
                        </div>
                        <div className="w-10" />
                    </div>
                    <div className="flex items-center justify-center gap-2 mt-2">
                        <p className={`text-xs ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>Select a topic to start studying</p>
                        {topics.length > 5 && (
                            <button 
                                onClick={handleRandomTopic}
                                className="flex items-center gap-1 px-3 py-1.5 bg-instacart-purple-light hover:bg-instacart-purple rounded-full transition-colors text-xs font-semibold"
                                title="Pick a random topic"
                            >
                                <Shuffle size={14} className="text-instacart-purple" />
                                <span className="text-instacart-purple">Random</span>
                            </button>
                        )}
                    </div>
                </header>

                <div className="p-4 space-y-3">
                    {topics.length === 0 ? (
                        <div className={`text-center py-20 italic text-sm ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                            No topics found for this subject.
                        </div>
                    ) : (
                        topics.map((topic) => (
                            <div
                                key={topic.id}
                                onClick={() => setSelectedTopic(topic)}
                                className={`rounded-2xl border p-4 cursor-pointer hover:border-instacart-green transition-all shadow-sm ${
                                    isDarkMode 
                                        ? 'bg-instacart-dark-card border-instacart-dark-border' 
                                        : 'bg-white border-instacart-border'
                                }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0 mr-3">
                                        <h3 className={`font-bold leading-tight ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{topic.name}</h3>
                                        {topic.description && (
                                            <p className={`text-xs mt-1 line-clamp-2 ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>{topic.description}</p>
                                        )}
                                        <div className="flex items-center space-x-2 mt-2">
                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${DIFFICULTY_COLORS[topic.difficulty_level] || (isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600')}`}>
                                                {topic.difficulty_level}
                                            </span>
                                            <span className={`flex items-center text-[10px] font-semibold ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                                                <Clock size={10} className="mr-1" />
                                                {topic.estimated_study_mins} mins
                                            </span>
                                            <span className={`flex items-center text-[10px] font-semibold ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                                                <BarChart2 size={10} className="mr-1" />
                                                {topic.question_count} Qs
                                            </span>
                                        </div>
                                    </div>
                                    <div className={`p-2.5 rounded-full flex-shrink-0 ${isDarkMode ? 'bg-instacart-green-light/20' : 'bg-instacart-green-light'}`}>
                                        <Play size={16} className="text-instacart-green" fill="currentColor" />
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
                    isDarkMode={isDarkMode}
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
