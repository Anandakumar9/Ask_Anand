'use client';

import React, { useEffect, useState } from 'react';
import { Search, MapPin, ChevronRight, BookOpen, Globe, Landmark, TrendingUp, Play, Loader2, Trophy, User } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/store/useStore';
import { dashboardApi, profileApi, leaderboardApi } from '@/services/api';

type Tab = 'home' | 'study' | 'rank' | 'profile';

// ── Rank tab ──────────────────────────────────────────────────
function RankView() {
  const { user } = useStore();
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    leaderboardApi.getLeaderboard(20)
      .then(r => setEntries(r.data?.leaderboard ?? r.data ?? []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex-1 flex items-center justify-center py-20">
      <Loader2 className="animate-spin text-instacart-green" size={40} />
    </div>
  );

  return (
    <div className="p-4 space-y-4">
      <div className="text-center py-2">
        <h2 className="text-xl font-black text-instacart-dark">Leaderboard</h2>
        <p className="text-xs text-instacart-grey mt-1">Ranked by stars earned</p>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-16 text-instacart-grey italic text-sm">No rankings yet — complete tests to earn stars!</div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry: any) => {
            const isMe = entry.user_id === user?.id;
            const medal = entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : null;
            return (
              <div
                key={entry.user_id}
                className={`flex items-center gap-3 px-4 py-3 rounded-2xl border ${isMe ? 'border-instacart-green bg-instacart-green-light' : 'bg-white border-instacart-border'}`}
              >
                <span className="text-base font-black w-8 text-center text-instacart-dark">
                  {medal ?? `#${entry.rank}`}
                </span>
                <div className="h-9 w-9 rounded-full bg-instacart-green flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {(entry.username || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`font-bold text-sm truncate ${isMe ? 'text-instacart-green' : 'text-instacart-dark'}`}>
                    {entry.username}{isMe ? ' (You)' : ''}
                  </p>
                  <p className="text-[10px] text-instacart-grey font-semibold">{entry.test_count} tests · {entry.accuracy}% avg</p>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-sm font-black text-instacart-dark">{entry.stars}</span>
                  <span className="text-base">⭐</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Profile tab ───────────────────────────────────────────────
function ProfileView() {
  const { user, logout } = useStore();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    profileApi.getStats()
      .then(r => setStats(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => { logout(); router.push('/login'); };

  return (
    <div className="p-4 space-y-4 pb-10">
      {/* Avatar + name */}
      <div className="flex flex-col items-center py-6 gap-3">
        <div className="h-20 w-20 rounded-full bg-instacart-green flex items-center justify-center text-white font-black text-3xl shadow-lg">
          {user?.name?.charAt(0) ?? 'U'}
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl text-instacart-dark">{user?.name}</h2>
          <p className="text-xs text-instacart-grey mt-0.5">{user?.email}</p>
        </div>
      </div>

      {/* Stats cards */}
      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="animate-spin text-instacart-green" size={32} /></div>
      ) : stats ? (
        <>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-2xl border border-instacart-border p-3 text-center shadow-sm">
              <span className="block text-xl mb-1">⭐</span>
              <span className="block font-black text-instacart-dark">{stats.basic_info?.total_stars ?? 0}</span>
              <span className="text-[10px] uppercase text-instacart-grey font-bold">Stars</span>
            </div>
            <div className="bg-white rounded-2xl border border-instacart-border p-3 text-center shadow-sm">
              <span className="block text-xl mb-1">🔥</span>
              <span className="block font-black text-instacart-dark">{stats.study_streak ?? 0}</span>
              <span className="text-[10px] uppercase text-instacart-grey font-bold">Streak</span>
            </div>
            <div className="bg-white rounded-2xl border border-instacart-border p-3 text-center shadow-sm">
              <span className="block text-xl mb-1">📝</span>
              <span className="block font-black text-instacart-dark">{stats.activity_stats?.total_tests ?? 0}</span>
              <span className="text-[10px] uppercase text-instacart-grey font-bold">Tests</span>
            </div>
          </div>

          {/* Performance */}
          {stats.recent_performance && stats.recent_performance.length > 0 && (
            <div className="bg-white rounded-2xl border border-instacart-border p-4 shadow-sm">
              <h3 className="font-bold text-instacart-dark mb-3">Recent Performance</h3>
              <div className="space-y-2">
                {stats.recent_performance.slice(0, 4).map((p: any, i: number) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-xs text-instacart-grey truncate flex-1 mr-2">{p.topic_name || 'Test'}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${p.score >= 70 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {p.score?.toFixed(0)}%
                    </span>
                    {p.star_earned && <span className="ml-1 text-sm">⭐</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-4 text-instacart-grey text-sm">Could not load profile stats.</div>
      )}

      <button
        onClick={handleLogout}
        className="w-full mt-4 py-4 rounded-2xl border border-red-200 text-red-500 font-bold text-sm bg-red-50 active:scale-95 transition-all"
      >
        Log Out
      </button>
    </div>
  );
}

// ── Main Home Page ────────────────────────────────────────────
export default function Home() {
  const router = useRouter();
  const { user, token, logout, hasHydrated } = useStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('home');

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
        logout();
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [token, router, logout, hasHydrated]);

  if (!mounted || !hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <Loader2 className="animate-spin text-instacart-green mx-auto mb-4" size={48} />
          <p className="text-instacart-grey font-semibold">Loading...</p>
        </div>
      </div>
    );
  }

  if (!token || loading || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="animate-spin text-instacart-green" size={48} />
      </div>
    );
  }

  const { stats, recent_activity, continue_topic, performance_goal } = data;

  const NAV: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'home', label: 'Home', icon: <Globe size={20} /> },
    { id: 'study', label: 'Study', icon: <BookOpen size={20} /> },
    { id: 'rank', label: 'Rank', icon: <Trophy size={20} /> },
    { id: 'profile', label: 'Profile', icon: <User size={20} /> },
  ];

  return (
    <main className="min-h-screen bg-instacart-grey-light pb-24">
      {/* ── Home Tab ───────────────────────────────────────── */}
      {activeTab === 'home' && (
        <>
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
                onClick={() => setActiveTab('profile')}
                className="h-10 w-10 rounded-full bg-instacart-green-light flex items-center justify-center border border-instacart-green text-instacart-green font-bold hover:bg-instacart-green hover:text-white transition-all"
              >
                {user?.name.charAt(0)}
              </button>
            </div>

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
            {continue_topic ? (
              <section>
                <div className="bg-instacart-green rounded-2xl p-5 text-white shadow-lg relative overflow-hidden">
                  <h2 className="text-lg font-bold mb-1">Continue studying</h2>
                  <p className="text-sm opacity-90 mb-4">{continue_topic.topic_name} ({continue_topic.subject_name})</p>
                  <div className="flex items-center bg-white/20 rounded-full h-2 w-full mb-6">
                    <div className="bg-white h-full rounded-full transition-all duration-1000" style={{ width: `${continue_topic.progress}%` }} />
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
                  <button onClick={() => router.push('/setup')} className="bg-white text-instacart-green px-6 py-2 rounded-full font-bold">
                    Get Started
                  </button>
                </div>
              </section>
            )}

            {/* Stats Row */}
            <section className="grid grid-cols-3 gap-3">
              <div className="card text-center py-4 bg-orange-50 border-orange-100">
                <span className="block text-2xl mb-1">⭐</span>
                <span className="block font-bold text-instacart-dark">{stats.stars}</span>
                <span className="text-[10px] uppercase text-instacart-grey font-bold">Stars</span>
              </div>
              <div className="card text-center py-4 bg-blue-50 border-blue-100">
                <span className="block text-2xl mb-1">🔥</span>
                <span className="block font-bold text-instacart-dark">{stats.study_streak} Days</span>
                <span className="text-[10px] uppercase text-instacart-grey font-bold">Streak</span>
              </div>
              <div className="card text-center py-4 bg-green-50 border-green-100">
                <span className="block text-2xl mb-1">📈</span>
                <span className="block font-bold text-instacart-dark">{performance_goal?.current ?? 0}%</span>
                <span className="text-[10px] uppercase text-instacart-grey font-bold">Avg Score</span>
              </div>
            </section>

            {/* Popular Subjects */}
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
              </div>
              <div className="space-y-3">
                {recent_activity.length > 0 ? (
                  recent_activity.map((activity: any, i: number) => (
                    <div key={i} className="card flex items-center p-3">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center mr-4 ${activity.type === 'test' ? 'bg-instacart-green-light text-instacart-green' : 'bg-blue-50 text-blue-500'}`}>
                        {activity.type === 'test' ? <Landmark size={18} /> : <BookOpen size={18} />}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-bold text-sm text-instacart-dark leading-tight">
                          {activity.type === 'test' ? 'Mock Test' : 'Study Session'} — {activity.topic_name}
                        </h4>
                        <p className="text-[10px] text-instacart-grey font-semibold mt-0.5">
                          {activity.subject_name} • {new Date(activity.timestamp).toLocaleDateString()} • {
                            activity.type === 'test' ? `Score: ${activity.score?.toFixed(0)}%` : `${activity.duration_mins ?? '—'} mins`
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
        </>
      )}

      {/* ── Study Tab ──────────────────────────────────────── */}
      {activeTab === 'study' && (
        <div className="flex flex-col min-h-screen">
          <header className="p-4 bg-white border-b border-instacart-border">
            <h1 className="font-bold text-xl text-instacart-dark text-center">Study</h1>
          </header>
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center space-y-4">
              <div className="text-5xl">📚</div>
              <h2 className="text-xl font-bold text-instacart-dark">Pick a Topic</h2>
              <p className="text-instacart-grey text-sm">Browse exams and subjects to find what you want to study.</p>
              <button
                onClick={() => router.push('/setup')}
                className="bg-instacart-green text-white font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all shadow-md"
              >
                Browse Topics
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Rank Tab ───────────────────────────────────────── */}
      {activeTab === 'rank' && <RankView />}

      {/* ── Profile Tab ────────────────────────────────────── */}
      {activeTab === 'profile' && <ProfileView />}

      {/* ── Bottom Nav ─────────────────────────────────────── */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-instacart-border flex justify-around items-center p-3 z-10 shadow-lg">
        {NAV.map(({ id, label, icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex flex-col items-center transition-colors ${active ? 'text-instacart-green' : 'text-instacart-grey'}`}
            >
              <div className={`p-2 rounded-full mb-1 ${active ? 'bg-instacart-green-light' : ''}`}>
                {icon}
              </div>
              <span className="text-[10px] font-bold">{label}</span>
            </button>
          );
        })}
      </nav>
    </main>
  );
}
