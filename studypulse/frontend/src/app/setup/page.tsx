'use client';

import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, CheckCircle2, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { examApi, authApi } from '@/services/api';

export default function ExamSelection() {
    const router = useRouter();
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
            <div className="min-h-screen flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-instacart-green" size={48} />
            </div>
        );
    }

    return (
        <main className="min-h-screen bg-white pb-24">
            <header className="p-4 border-b border-instacart-border flex items-center bg-white sticky top-0 z-10">
                <button onClick={() => router.back()} className="p-2 hover:bg-instacart-grey-light rounded-full transition-colors">
                    <ChevronLeft className="text-instacart-dark" />
                </button>
                <h1 className="flex-1 text-center font-bold text-lg text-instacart-dark">Select Your Exam</h1>
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
                        className="block w-full pl-10 pr-3 py-3 border border-instacart-border rounded-xl bg-instacart-grey-light text-sm focus:outline-none focus:ring-2 focus:ring-instacart-green focus:bg-white transition-all shadow-sm"
                        placeholder="Search exams..."
                    />
                </div>

                {categories.map(category => {
                    const catExams = filteredExams.filter(e => (e.category || 'Other') === category);
                    if (catExams.length === 0) return null;

                    return (
                        <section key={category}>
                            <h3 className="text-xs font-bold text-instacart-grey uppercase tracking-wider mb-3 px-1">{category} Exams</h3>
                            <div className="grid grid-cols-2 gap-3 px-1">
                                {catExams.map(exam => (
                                    <div
                                        key={exam.id}
                                        onClick={() => setSelected(exam.id)}
                                        className={`card p-4 cursor-pointer relative transition-all ${selected === exam.id ? 'border-instacart-green bg-instacart-green-light shadow-instacart-hover ring-1 ring-instacart-green' : 'hover:border-instacart-green'
                                            }`}
                                    >
                                        <div className="text-3xl mb-3">🎓</div>
                                        <h4 className="font-bold text-instacart-dark text-sm leading-tight mb-1 h-10 line-clamp-2">{exam.name}</h4>
                                        <p className="text-[10px] font-bold text-instacart-green bg-instacart-green-light px-2 py-0.5 rounded-full inline-block">
                                            {exam.subject_count} Subjects
                                        </p>

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
                    <div className="text-center py-20 text-instacart-grey italic">
                        No exams found matching &quot;{search}&quot;
                    </div>
                )}
            </div>

            <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-instacart-border bg-opacity-90 backdrop-blur-sm">
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
                    className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all flex items-center justify-center ${selected ? 'bg-instacart-green text-white hover:bg-instacart-green-dark active:scale-95' : 'bg-instacart-border text-instacart-grey cursor-not-allowed'
                        }`}
                >
                    {loading ? <Loader2 className="animate-spin" /> : 'Continue'}
                </button>
            </div>
        </main>
    );
}
