'use client';

import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, CheckCircle2, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { examApi, authApi } from '@/services/api';
import { useThemeStore } from '@/store/themeStore';

export default function ExamSelection() {
    const router = useRouter();
    const { isDarkMode } = useThemeStore();
    const [selected, setSelected] = useState<number | null>(null);
    const [exams, setExams] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchExams = async () => {
            try {
                const response = await examApi.getExams();
                setExams(response.data);
            } catch (err) {
                console.error('Failed to fetch exams', err);
            } finally {
                setLoading(false);
            }
        };
        fetchExams();
    }, []);

    const filteredExams = exams.filter(e =>
        e.name.toLowerCase().includes(search.toLowerCase()) ||
        (e.category && e.category.toLowerCase().includes(search.toLowerCase()))
    );

    const categories = Array.from(new Set(exams.map(e => e.category || 'Other')));

    if (loading) {
        return (
            <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <main className={`min-h-screen pb-24 ${isDarkMode ? 'bg-instacart-dark-bg' : 'bg-white'}`}>
            <header className={`p-4 border-b flex items-center sticky top-0 z-10 ${isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'}`}>
                <button onClick={() => router.back()} className={`p-2 rounded-full transition-colors ${isDarkMode ? 'hover:bg-instacart-dark-border' : 'hover:bg-instacart-grey-light'}`} title="Go back">
                    <ChevronLeft className={isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'} />
                </button>
                <h1 className={`flex-1 text-center font-bold text-lg ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>Select Your Exam</h1>
                <div className="w-10" />
            </header>

            <div className="p-4 space-y-6">
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-instacart-grey" />
                    </div>
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className={`block w-full pl-10 pr-3 py-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-instacart-green transition-all shadow-sm ${
                            isDarkMode 
                                ? 'bg-instacart-dark-card border-instacart-dark-border text-instacart-dark-text placeholder-instacart-dark-text-secondary focus:bg-instacart-dark-card' 
                                : 'bg-instacart-grey-light border-instacart-border text-instacart-dark focus:bg-white'
                        }`}
                        placeholder="Search exams..."
                    />
                </div>

                {categories.map(category => {
                    const catExams = filteredExams.filter(e => (e.category || 'Other') === category);
                    if (catExams.length === 0) return null;

                    return (
                        <section key={category}>
                            <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 px-1 ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>{category} Exams</h3>
                            <div className="grid grid-cols-2 gap-3 px-1">
                                {catExams.map(exam => (
                                    <div
                                        key={exam.id}
                                        onClick={() => setSelected(exam.id)}
                                        className={`card p-4 cursor-pointer relative transition-all ${
                                            isDarkMode
                                                ? selected === exam.id 
                                                    ? 'border-instacart-green bg-instacart-green-light/20 shadow-instacart-hover ring-1 ring-instacart-green' 
                                                    : 'hover:border-instacart-green bg-instacart-dark-card border-instacart-dark-border'
                                                : selected === exam.id
                                                    ? 'border-instacart-green bg-instacart-green-light shadow-instacart-hover ring-1 ring-instacart-green'
                                                    : 'hover:border-instacart-green bg-white border-instacart-border'
                                        }`}
                                    >
                                        <div className="text-3xl mb-3">🎓</div>
                                        <h4 className={`font-bold text-sm leading-tight mb-1 h-10 line-clamp-2 ${isDarkMode ? 'text-instacart-dark-text' : 'text-instacart-dark'}`}>{exam.name}</h4>
                                        <div className="flex items-center gap-2">
                                            <p className="text-[10px] font-bold text-instacart-green bg-instacart-green-light px-2 py-0.5 rounded-full">
                                                {exam.subject_count} Subjects
                                            </p>
                                            <p className="text-[10px] font-bold text-instacart-blue bg-blue-50 px-2 py-0.5 rounded-full">
                                                {exam.total_questions} Questions
                                            </p>
                                        </div>

                                        {selected === exam.id && (
                                            <div className="absolute top-2 right-2 text-instacart-green">
                                                <CheckCircle2 size={20} fill="#E8F5E3" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    );
                })}

                {filteredExams.length === 0 && (
                    <div className={`text-center py-20 italic ${isDarkMode ? 'text-instacart-dark-text-secondary' : 'text-instacart-grey'}`}>
                        No exams found matching &quot;{search}&quot;
                    </div>
                )}
            </div>

            <div className={`fixed bottom-0 left-0 right-0 p-4 border-t bg-opacity-90 backdrop-blur-sm ${
                isDarkMode ? 'bg-instacart-dark-card border-instacart-dark-border' : 'bg-white border-instacart-border'
            }`}>
                <button
                    disabled={!selected || loading}
                    onClick={async () => {
                        if (selected) {
                            setLoading(true);
                            try {
                                await authApi.updateProfile({ target_exam_id: selected });
                                router.push(`/subjects?examId=${selected}`);
                            } catch (err) {
                                console.error('Failed to save exam selection', err);
                                alert('Failed to save selection. Please try again.');
                            } finally {
                                setLoading(false);
                            }
                        }
                    }}
                    className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all flex items-center justify-center ${
                        selected 
                            ? 'bg-instacart-green text-white hover:bg-instacart-green-dark active:scale-95' 
                            : isDarkMode ? 'bg-instacart-dark-border text-instacart-dark-text-secondary cursor-not-allowed' : 'bg-instacart-border text-instacart-grey cursor-not-allowed'
                    }`}
                >
                    {loading ? <Loader2 className="animate-spin" /> : 'Continue'}
                </button>
            </div>
        </main>
    );
}
