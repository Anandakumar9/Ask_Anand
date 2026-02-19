'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { ChevronLeft, ChevronRight, BookOpen, Loader2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { examApi } from '@/services/api';

function SubjectsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const examId = searchParams.get('examId');

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
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <main className="min-h-screen bg-instacart-grey-light pb-8">
            <header className="p-4 border-b border-instacart-border flex items-center bg-white sticky top-0 z-10">
                <button onClick={() => router.back()} className="p-2 hover:bg-instacart-grey-light rounded-full transition-colors">
                    <ChevronLeft className="text-instacart-dark" />
                </button>
                <div className="flex-1 text-center">
                    <h1 className="font-bold text-lg text-instacart-dark">{examName}</h1>
                    <p className="text-xs text-instacart-grey">Select a subject to study</p>
                </div>
                <div className="w-10" />
            </header>

            <div className="p-4 space-y-3">
                {subjects.length === 0 ? (
                    <div className="text-center py-20 text-instacart-grey italic text-sm">
                        No subjects found for this exam.
                    </div>
                ) : (
                    subjects.map((subject) => (
                        <div
                            key={subject.id}
                            onClick={() => router.push(`/topics?examId=${examId}&subjectId=${subject.id}&subjectName=${encodeURIComponent(subject.name)}`)}
                            className="bg-white rounded-2xl border border-instacart-border p-4 flex items-center cursor-pointer hover:border-instacart-green transition-all shadow-sm"
                        >
                            <div className="h-11 w-11 rounded-xl bg-instacart-green-light flex items-center justify-center mr-4 text-instacart-green flex-shrink-0">
                                <BookOpen size={22} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="font-bold text-instacart-dark leading-tight">{subject.name}</h3>
                                <p className="text-xs text-instacart-grey mt-0.5">{subject.topic_count} Topics</p>
                            </div>
                            <ChevronRight size={18} className="text-instacart-grey flex-shrink-0" />
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
