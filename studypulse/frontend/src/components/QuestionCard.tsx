'use client';

import React, { useState, useMemo } from 'react';
import { 
    CheckCircle2, 
    XCircle, 
    Clock, 
    BookOpen, 
    Image as ImageIcon,
    Volume2,
    Video,
    ChevronDown,
    ChevronUp
} from 'lucide-react';

/**
 * Types for question data with image support
 */

interface OptionData {
    text: string;
    image?: string | null;
}

type OptionValue = string | OptionData;

interface Question {
    id: number;
    question_text: string;
    options: Record<string, OptionValue>;
    correct_answer: string;
    explanation?: string | null;
    difficulty?: string;
    source?: string;
    question_images?: string[];
    explanation_images?: string[];
    audio_url?: string | null;
    video_url?: string | null;
}

interface QuestionCardProps {
    question: Question;
    questionNumber: number;
    totalQuestions: number;
    selectedAnswer?: string | null;
    showResult?: boolean;
    onAnswerSelect?: (answer: string) => void;
    className?: string;
}

/**
 * Helper function to extract text from option value
 */
function getOptionText(option: OptionValue): string {
    if (typeof option === 'string') {
        return option;
    }
    return option.text || '';
}

/**
 * Helper function to extract image from option value
 */
function getOptionImage(option: OptionValue): string | null {
    if (typeof option === 'object' && option !== null && 'image' in option) {
        return option.image || null;
    }
    return null;
}

/**
 * Image Modal Component for full-size image viewing
 */
function ImageModal({ 
    src, 
    alt, 
    onClose 
}: { 
    src: string; 
    alt: string; 
    onClose: () => void;
}) {
    return (
        <div 
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
            onClick={onClose}
        >
            <div className="relative max-w-4xl max-h-[90vh]">
                <button
                    onClick={onClose}
                    className="absolute -top-10 right-0 text-white hover:text-gray-300"
                >
                    ✕ Close
                </button>
                <img
                    src={src}
                    alt={alt}
                    className="max-w-full max-h-[85vh] object-contain rounded-lg"
                />
            </div>
        </div>
    );
}

/**
 * Image Gallery Component
 */
function ImageGallery({ 
    images, 
    title 
}: { 
    images: string[]; 
    title: string;
}) {
    const [selectedImage, setSelectedImage] = useState<string | null>(null);

    if (!images || images.length === 0) return null;

    return (
        <div className="my-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <ImageIcon size={16} />
                <span>{title}</span>
            </div>
            <div className="flex flex-wrap gap-2">
                {images.map((img, idx) => (
                    <div
                        key={idx}
                        className="relative group cursor-pointer"
                        onClick={() => setSelectedImage(img)}
                    >
                        <img
                            src={img}
                            alt={`${title} ${idx + 1}`}
                            className="w-32 h-32 object-cover rounded-lg border border-gray-200 
                                     hover:border-blue-400 transition-colors"
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 
                                      transition-all rounded-lg flex items-center justify-center">
                            <span className="text-white opacity-0 group-hover:opacity-100 text-sm font-medium">
                                Click to enlarge
                            </span>
                        </div>
                    </div>
                ))}
            </div>
            
            {selectedImage && (
                <ImageModal
                    src={selectedImage}
                    alt={title}
                    onClose={() => setSelectedImage(null)}
                />
            )}
        </div>
    );
}

/**
 * Option Button Component
 */
function OptionButton({
    label,
    option,
    isSelected,
    isCorrect,
    showResult,
    onClick
}: {
    label: string;
    option: OptionValue;
    isSelected: boolean;
    isCorrect: boolean;
    showResult: boolean;
    onClick: () => void;
}) {
    const text = getOptionText(option);
    const image = getOptionImage(option);

    let buttonClass = 'w-full p-4 rounded-lg border-2 transition-all text-left';
    
    if (showResult) {
        if (isCorrect) {
            buttonClass += ' border-green-500 bg-green-50';
        } else if (isSelected && !isCorrect) {
            buttonClass += ' border-red-500 bg-red-50';
        } else {
            buttonClass += ' border-gray-200 bg-gray-50';
        }
    } else if (isSelected) {
        buttonClass += ' border-blue-500 bg-blue-50';
    } else {
        buttonClass += ' border-gray-200 hover:border-gray-300 hover:bg-gray-50';
    }

    return (
        <button
            onClick={onClick}
            disabled={showResult}
            className={buttonClass}
        >
            <div className="flex items-start gap-3">
                <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
                    ${showResult && isCorrect ? 'bg-green-500 text-white' : 
                      showResult && isSelected && !isCorrect ? 'bg-red-500 text-white' :
                      isSelected ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}>
                    {label}
                </span>
                <div className="flex-1">
                    <p className="text-gray-800">{text}</p>
                    {image && (
                        <img
                            src={image}
                            alt={`Option ${label}`}
                            className="mt-2 max-w-xs rounded-lg border border-gray-200"
                        />
                    )}
                </div>
                {showResult && isCorrect && (
                    <CheckCircle2 className="text-green-500 flex-shrink-0" size={20} />
                )}
                {showResult && isSelected && !isCorrect && (
                    <XCircle className="text-red-500 flex-shrink-0" size={20} />
                )}
            </div>
        </button>
    );
}

/**
 * Main QuestionCard Component
 */
export default function QuestionCard({
    question,
    questionNumber,
    totalQuestions,
    selectedAnswer,
    showResult = false,
    onAnswerSelect,
    className = ''
}: QuestionCardProps) {
    const [showExplanation, setShowExplanation] = useState(false);

    // Parse options
    const options = useMemo(() => {
        const opts: { label: string; value: OptionValue }[] = [];
        ['A', 'B', 'C', 'D'].forEach(label => {
            if (question.options[label]) {
                opts.push({ label, value: question.options[label] });
            }
        });
        return opts;
    }, [question.options]);

    // Difficulty badge color
    const difficultyColor = {
        easy: 'bg-green-100 text-green-800',
        medium: 'bg-yellow-100 text-yellow-800',
        hard: 'bg-red-100 text-red-800'
    }[question.difficulty || 'medium'];

    return (
        <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${className}`}>
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
                <div className="flex items-center justify-between">
                    <span className="text-white font-medium">
                        Question {questionNumber} of {totalQuestions}
                    </span>
                    <div className="flex items-center gap-2">
                        {question.difficulty && (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${difficultyColor}`}>
                                {question.difficulty}
                            </span>
                        )}
                        {question.source && (
                            <span className="px-2 py-1 bg-white/20 rounded-full text-xs text-white">
                                {question.source}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Question Content */}
            <div className="p-6">
                {/* Question Text */}
                <div className="mb-6">
                    <p className="text-lg text-gray-800 leading-relaxed">
                        {question.question_text}
                    </p>
                </div>

                {/* Question Images */}
                {question.question_images && question.question_images.length > 0 && (
                    <ImageGallery 
                        images={question.question_images} 
                        title="Question Images" 
                    />
                )}

                {/* Options */}
                <div className="space-y-3">
                    {options.map(({ label, value }) => (
                        <OptionButton
                            key={label}
                            label={label}
                            option={value}
                            isSelected={selectedAnswer === label}
                            isCorrect={question.correct_answer === label}
                            showResult={showResult}
                            onClick={() => onAnswerSelect?.(label)}
                        />
                    ))}
                </div>

                {/* Media Links */}
                {(question.audio_url || question.video_url) && (
                    <div className="mt-4 flex gap-4">
                        {question.audio_url && (
                            <a
                                href={question.audio_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-blue-600 hover:text-blue-700"
                            >
                                <Volume2 size={18} />
                                <span>Audio Explanation</span>
                            </a>
                        )}
                        {question.video_url && (
                            <a
                                href={question.video_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-blue-600 hover:text-blue-700"
                            >
                                <Video size={18} />
                                <span>Video Explanation</span>
                            </a>
                        )}
                    </div>
                )}

                {/* Explanation Section */}
                {showResult && question.explanation && (
                    <div className="mt-6">
                        <button
                            onClick={() => setShowExplanation(!showExplanation)}
                            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
                        >
                            <BookOpen size={18} />
                            <span>{showExplanation ? 'Hide' : 'Show'} Explanation</span>
                            {showExplanation ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                        
                        {showExplanation && (
                            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                                <div 
                                    className="text-gray-700 prose prose-sm max-w-none"
                                    dangerouslySetInnerHTML={{ __html: question.explanation }}
                                />
                                
                                {/* Explanation Images */}
                                {question.explanation_images && question.explanation_images.length > 0 && (
                                    <ImageGallery 
                                        images={question.explanation_images} 
                                        title="Explanation Images" 
                                    />
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * Compact Question Card for Lists
 */
export function QuestionCardCompact({
    question,
    onClick
}: {
    question: Question;
    onClick?: () => void;
}) {
    const hasImages = (question.question_images?.length ?? 0) > 0 || 
                      Object.values(question.options).some(opt => getOptionImage(opt) !== null);

    return (
        <div
            onClick={onClick}
            className="p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 
                     cursor-pointer transition-all hover:shadow-md"
        >
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                    <p className="text-gray-800 line-clamp-2">
                        {question.question_text}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                        {hasImages && (
                            <span className="flex items-center gap-1 text-xs text-gray-500">
                                <ImageIcon size={14} />
                                Has images
                            </span>
                        )}
                        <span className={`px-2 py-0.5 rounded text-xs ${
                            question.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                            question.difficulty === 'hard' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                        }`}>
                            {question.difficulty || 'medium'}
                        </span>
                    </div>
                </div>
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-700 font-medium">{question.correct_answer}</span>
                </div>
            </div>
        </div>
    );
}

/**
 * Question Type Definitions for Export
 */
export type { Question, OptionData, OptionValue };
