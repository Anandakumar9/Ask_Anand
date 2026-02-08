import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
    id: number;
    email: string;
    name: string;
    total_stars: number;
    target_exam_id?: number;
}

interface AppState {
    user: User | null;
    token: string | null;
    currentExamId: number | null;
    setUser: (user: User | null) => void;
    setToken: (token: string | null) => void;
    setCurrentExamId: (id: number | null) => void;
    logout: () => void;
    hasHydrated: boolean;
    setHasHydrated: (state: boolean) => void;
}

export const useStore = create<AppState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            currentExamId: null,
            setUser: (user) => set({ user }),
            setToken: (token) => set({ token }),
            setCurrentExamId: (id) => set({ currentExamId: id }),
            logout: () => set({ user: null, token: null, currentExamId: null }),
            hasHydrated: false,
            setHasHydrated: (state) => set({ hasHydrated: state }),
        }),
        {
            name: 'studypulse-storage',
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated(true);
            }
        }
    )
);
