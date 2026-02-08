'use client';

import React, { useEffect, useState } from 'react';
import { Search, MapPin, ChevronRight, BookOpen, Globe, Landmark, TrendingUp, Play, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/store/useStore';
import { dashboardApi } from '@/services/api';

export default function Home() {
  const router = useRouter();
  const { user, token, logout, hasHydrated } = useStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!hasHydrated) return;

    if (!token) {
      router.push('/login');
      return;
    }

    setLoading(true);
    const fetchDashboard = async () => {
      try {
        const response = await dashboardApi.getDashboard();
        setData(response.data);
      } catch (err) {
        console.error('Failed to fetch dashboard', err);
        // If unauthorized, logout
        logout();
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [token, router, logout]);

  if (!mounted || !hasHydrated || !token) return null;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="animate-spin text-instacart-green" size={48} />
      </div>
    );
  }

  const { stats, recent_activity, continue_topic } = data;

  return (
    <main className="min-h-screen bg-instacart-grey-light pb-24">
      {/* Header / Top Nav */}
      <header className="bg-white p-4 sticky top-0 z-10 border-b border-instacart-border shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-instacart-dark">Good Day, {user?.name.split(' ')[0]}! 👋</h1>
            <div className="flex items-center text-instacart-grey text-sm mt-0.5">
              <MapPin size={14} className="mr-1" />
              <span>Andhra Pradesh, India</span>
            </div>
          </div>
          <button
            onClick={() => { logout(); router.push('/login'); }}
            className="h-10 w-10 rounded-full bg-instacart-green-light flex items-center justify-center border border-instacart-green text-instacart-green font-bold hover:bg-instacart-green hover:text-white transition-all"
          >
            {user?.name.charAt(0)}
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-instacart-grey" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-3 border border-instacart-border rounded-full bg-instacart-grey-light text-sm focus:outline-none focus:ring-2 focus:ring-instacart-green focus:bg-white transition-all"
            placeholder="Search exams, subjects, topics..."
          />
        </div>
      </header>

      <div className="p-4 space-y-6">
        {/* Banner Section / Continue Studying */}
        {continue_topic ? (
          <section>
            <div className="bg-instacart-green rounded-2xl p-5 text-white shadow-lg relative overflow-hidden">
              <h2 className="text-lg font-bold mb-1">Continue studying</h2>
              <p className="text-sm opacity-90 mb-4">{continue_topic.topic_name} ({continue_topic.subject_name})</p>

              <div className="flex items-center bg-white/20 rounded-full h-2 w-full mb-6">
                <div className="bg-white h-full rounded-full transition-all duration-1000" style={{ width: `${continue_topic.progress}%` }}></div>
              </div>

              <button
                onClick={() => router.push(`/study?topicId=${continue_topic.topic_id}`)}
                className="bg-white text-instacart-green px-6 py-2 rounded-full font-bold flex items-center shadow-md hover:bg-instacart-grey-light transition-colors"
              >
                <Play size={16} className="mr-2 fill-current" />
                Resume ({continue_topic.progress}%)
              </button>
            </div>
          </section>
        ) : (
          <section>
            <div className="bg-instacart-green rounded-2xl p-6 text-white shadow-lg">
              <h2 className="text-xl font-bold mb-2">Ready to start?</h2>
              <p className="text-sm opacity-90 mb-4">Pick a topic and start your first study session.</p>
              <button
                onClick={() => router.push('/setup')}
                className="bg-white text-instacart-green px-6 py-2 rounded-full font-bold"
              >
                Get Started
              </button>
            </div>
          </section>
        )}

        {/* Stats Row */}
        <section className="grid grid-cols-3 gap-3">
          <div className="card text-center py-4 bg-orange-50 border-orange-100">
            <span className="block text-2xl mb-1">⭐</span>
            <span className="block font-bold text-instacart-dark">{stats.total_stars}</span>
            <span className="text-[10px] uppercase text-instacart-grey font-bold">Stars</span>
          </div>
          <div className="card text-center py-4 bg-blue-50 border-blue-100">
            <span className="block text-2xl mb-1">🔥</span>
            <span className="block font-bold text-instacart-dark">{stats.study_streak} Days</span>
            <span className="text-[10px] uppercase text-instacart-grey font-bold">Streak</span>
          </div>
          <div className="card text-center py-4 bg-green-50 border-green-100">
            <span className="block text-2xl mb-1">📈</span>
            <span className="block font-bold text-instacart-dark">{stats.average_score}%</span>
            <span className="text-[10px] uppercase text-instacart-grey font-bold">Avg Score</span>
          </div>
        </section>

        {/* Popular Subjects (Placeholder for now) */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-instacart-dark">Popular Subjects</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              { name: 'Geography', icon: <Globe />, color: 'bg-blue-100 text-blue-600' },
              { name: 'History', icon: <BookOpen />, color: 'bg-orange-100 text-orange-600' },
              { name: 'Polity', icon: <Landmark />, color: 'bg-purple-100 text-purple-600' },
              { name: 'Economy', icon: <TrendingUp />, color: 'bg-green-100 text-green-600' },
            ].map((subject) => (
              <div key={subject.name} className="card flex items-center p-3 cursor-pointer hover:border-instacart-green transition-all">
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center mr-3 ${subject.color}`}>
                  {subject.icon}
                </div>
                <span className="font-semibold text-instacart-dark">{subject.name}</span>
                <ChevronRight size={16} className="ml-auto text-instacart-grey" />
              </div>
            ))}
          </div>
        </section>

        {/* Start Fresh Section if no continue topic */}
        {!continue_topic && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-instacart-dark">Top Topics for You</h3>
            </div>
            <div className="space-y-3">
              {[
                { id: 1, name: 'Physical Geography of India', sub: 'Geography' },
                { id: 6, name: 'Ancient India', sub: 'History' }
              ].map(topic => (
                <div
                  key={topic.id}
                  onClick={() => router.push(`/study?topicId=${topic.id}`)}
                  className="card flex items-center justify-between p-4 cursor-pointer hover:border-instacart-green"
                >
                  <div>
                    <h4 className="font-bold text-instacart-dark">{topic.name}</h4>
                    <p className="text-xs text-instacart-grey">{topic.sub}</p>
                  </div>
                  <div className="bg-instacart-green-light p-2 rounded-full text-instacart-green">
                    <Play size={16} fill="currentColor" />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Recent Activity */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-instacart-dark">Recent Activity</h3>
            <button className="text-instacart-green font-semibold text-sm">View History</button>
          </div>
          <div className="space-y-3">
            {recent_activity.length > 0 ? (
              recent_activity.map((activity: any, i: number) => (
                <div key={i} className="card flex items-center p-3">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center mr-4 ${activity.type === 'test' ? 'bg-instacart-green-light text-instacart-green' : 'bg-blue-50 text-blue-500'
                    }`}>
                    {activity.type === 'test' ? <Landmark size={18} /> : <BookOpen size={18} />}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-sm text-instacart-dark leading-tight">{activity.title}</h4>
                    <p className="text-[10px] text-instacart-grey font-semibold mt-0.5">
                      {new Date(activity.timestamp).toLocaleDateString()} • {
                        activity.type === 'test' ? `Score: ${activity.score}%` : `${activity.duration_mins} mins`
                      } {activity.star_earned && '⭐'}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-instacart-border" />
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-instacart-grey italic text-sm">No recent activity yet.</div>
            )}
          </div>
        </section>
      </div>

      {/* Bottom Nav (Same as before) */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-instacart-border flex justify-around items-center p-3 z-10 shadow-lg">
        <div className="flex flex-col items-center text-instacart-green">
          <div className="bg-instacart-green-light p-2 rounded-full mb-1">
            <Globe size={20} />
          </div>
          <span className="text-[10px] font-bold">Home</span>
        </div>
        <div className="flex flex-col items-center text-instacart-grey" onClick={() => router.push('/setup')}>
          <div className="p-2 rounded-full mb-1">
            <BookOpen size={20} />
          </div>
          <span className="text-[10px] font-bold">Study</span>
        </div>
        <div className="flex flex-col items-center text-instacart-grey">
          <div className="p-2 rounded-full mb-1">
            <Landmark size={20} />
          </div>
          <span className="text-[10px] font-bold">Tests</span>
        </div>
        <div className="flex flex-col items-center text-instacart-grey">
          <div className="p-2 rounded-full mb-1">
            <Search size={20} />
          </div>
          <span className="text-[10px] font-bold">Search</span>
        </div>
        <div className="flex flex-col items-center text-instacart-grey">
          <div className="p-2 rounded-full mb-1">
            <Globe size={20} />
          </div>
          <span className="text-[10px] font-bold">Profile</span>
        </div>
      </nav>
    </main>
  );
}
