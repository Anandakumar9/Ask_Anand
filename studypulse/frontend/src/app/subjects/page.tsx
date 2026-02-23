'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, ChevronRight, BookOpen, Loader2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { examApi } from '@/services/api';
import { useThemeStore } from '@/store/themeStore';

function SubjectsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const examId = searchParams.get('examId');
    const { isDarkMode } = useThemeStore();

    const [subjects, setSubjects] = useState<any[]>([]);
    const [examName, setExamName] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!examId) {
            router.push('/setup');
            return;
        }

        const fetchData = async () => {
            try {
                const [examRes, subjectsRes] = await Promise.all([
                    examApi.getExamDetails(parseInt(examId)),
                    examApi.getSubjects(parseInt(examId)),
                ]);
                setExamName(examRes.data.name);
                setSubjects(subjectsRes.data);
            } catch (err) {
                console.error('Failed to fetch subjects', err);
                router.push('/setup');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [examId, router]);

    if (loading) {
        return (
            <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <main className={`min-h-screen pb-8 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-instacart-grey-light'}`}>
            <header className={`p-4 border-b flex items-center sticky top-0 z-10 ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                <button onClick={() => router.back()} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go back">
                    <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                </button>
                <div className="flex-1 text-center">
                    <h1 className={`font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{examName}</h1>
                    <p className={`text-xs ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>Select a subject to study</p>
                </div>
                <div className="w-10" />
            </header>

            <div className="p-4 space-y-3">
                {subjects.length === 0 ? (
                    <div className={`text-center py-20 italic ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                        No subjects found for this exam.
                    </div>
                ) : (
                    subjects.map((subject) => (
                        <div
                            key={subject.id}
                            onClick={() => router.push(`/topics?examId=${examId}&subjectId=${subject.id}&subjectName=${encodeURIComponent(subject.name)}`)}
                            className={`flex items-center cursor-pointer transition-all shadow-sm ${
                                isDarkMode 
                                    ? 'bg-instacart-dark-card border border-instacart-dark-border hover:border-instacart-green' 
                                    : 'bg-white border border-instacart-border hover:border-instacart-green'
                            } rounded-2xl p-4`}
                        >
                            <div className={`h-11 w-11 rounded-xl flex items-center justify-center mr-4 text-instacart-green flex-shrink-0 ${isDarkMode ? 'bg-instacart-green-light/20' : 'bg-instacart-green-light'}`}>
                                <BookOpen size={22} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className={`font-bold leading-tight ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{subject.name}</h3>
                                <p className={`text-xs mt-0.5 ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>{subject.topic_count} Topics</p>
                            </div>
                            <ChevronRight size={18} className={isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'} />
                        </div>
                    ))
                )}
            </div>
        </main>
    );
}

export default function SubjectsPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        }>
            <SubjectsContent />
        </Suspense>
    );
}
