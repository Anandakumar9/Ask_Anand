import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../api/api_service.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  final _api = ApiService();
  Map<String, dynamic>? _dashboardData;
  List<Map<String, dynamic>> _weeklyStats = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchProgress();
  }

  Future<void> _fetchProgress() async {
    setState(() => _loading = true);
    try {
      final dashRes = await _api.getDashboard();
      final weekRes = await _api.getWeeklyStats();

      final weeklyRaw = weekRes.data['weekly_stats'] as List? ?? [];
      setState(() {
        _dashboardData = dashRes.data;
        _weeklyStats =
            weeklyRaw.map((e) => Map<String, dynamic>.from(e)).toList();
        _loading = false;
      });
    } catch (e) {
      debugPrint('Progress fetch error: $e');
      setState(() {
        _dashboardData = {
          'stats': {
            'total_stars': 0,
            'average_score': 0,
            'study_streak': 0,
            'total_study_hours': 0,
            'tests_completed': 0,
            'tests_passed': 0,
          },
          'recent_activity': [],
        };
        _weeklyStats = [];
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F7),
      appBar: AppBar(title: const Text('Your Goals')),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF43B02A)))
          : RefreshIndicator(
              onRefresh: _fetchProgress,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildPerformanceHeader(),
                  const SizedBox(height: 16),
                  _buildMetricCards(),
                  const SizedBox(height: 24),
                  _buildStreakSection(),
                  const SizedBox(height: 24),
                  _buildSubjectProficiency(),
                  const SizedBox(height: 24),
                  _buildWeeklyChart(),
                ],
              ),
            ),
    );
  }

  // ── Performance Tracking header ──────────────────────────────────
  Widget _buildPerformanceHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: const [
          Icon(LucideIcons.barChart2, color: Color(0xFF43B02A)),
          SizedBox(width: 10),
          Text(
            'PERFORMANCE TRACKING',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Color(0xFF43B02A),
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }

  // ── Accuracy / Growth / Stars metric cards ─────────────────────
  Widget _buildMetricCards() {
    final stats = _dashboardData?['stats'] ?? {};
    final avgScore = (stats['average_score'] ?? 0).toDouble();
    final testsCompleted = stats['tests_completed'] ?? 0;
    final testsPassed = stats['tests_passed'] ?? 0;
    final passRate =
        testsCompleted > 0 ? ((testsPassed / testsCompleted) * 100).round() : 0;
    final totalStars = stats['total_stars'] ?? 0;

    return Row(
      children: [
        _metricCard(
          icon: LucideIcons.target,
          iconColor: Colors.blue,
          bg: const Color(0xFFEFF6FF),
          label: 'ACCURACY',
          value: '${avgScore.round()}%',
        ),
        const SizedBox(width: 8),
        _metricCard(
          icon: LucideIcons.trendingUp,
          iconColor: const Color(0xFF43B02A),
          bg: const Color(0xFFF0FDF4),
          label: 'PASS RATE',
          value: '$passRate%',
        ),
        const SizedBox(width: 8),
        _metricCard(
          icon: LucideIcons.star,
          iconColor: Colors.orange,
          bg: const Color(0xFFFFF7ED),
          label: 'STARS',
          value: '$totalStars',
        ),
      ],
    );
  }

  Widget _metricCard({
    required IconData icon,
    required Color iconColor,
    required Color bg,
    required String label,
    required String value,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.black.withOpacity(0.05)),
        ),
        child: Column(
          children: [
            Icon(icon, color: iconColor, size: 22),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.bold,
                color: Color(0xFF767676),
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Study Streak (like Firebase Goals) ─────────────────────────
  Widget _buildStreakSection() {
    final stats = _dashboardData?['stats'] ?? {};
    final streak = stats['study_streak'] ?? 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('🔥', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                Text(
                  'Study Streak',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF7ED),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '$streak day${streak == 1 ? '' : 's'}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.deepOrange,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // 7-day visual streak
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: List.generate(7, (i) {
                final dayNames = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
                final active = i < streak;
                return Column(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: active
                            ? const Color(0xFF43B02A)
                            : const Color(0xFFF0F0F0),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: active
                            ? const Icon(Icons.check,
                                color: Colors.white, size: 18)
                            : null,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      dayNames[i],
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: active
                            ? const Color(0xFF43B02A)
                            : const Color(0xFF767676),
                      ),
                    ),
                  ],
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  // ── Subject Proficiency (like Firebase) ────────────────────────
  Widget _buildSubjectProficiency() {
    // Build subject-level scores from recent activity (tests)
    final activity =
        (_dashboardData?['recent_activity'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final testActivities = activity.where((a) => a['type'] == 'test').toList();

    // Aggregate scores by subject extracted from title
    final Map<String, List<double>> subjectScores = {};
    for (var a in testActivities) {
      final title = (a['title'] ?? '') as String;
      // Title pattern: "Mock Test - TopicName"
      final subject = title.replaceFirst('Mock Test - ', '');
      final score = (a['score'] ?? 0).toDouble();
      subjectScores.putIfAbsent(subject, () => []).add(score);
    }

    final proficiencies = subjectScores.entries.map((e) {
      final avg = e.value.reduce((a, b) => a + b) / e.value.length;
      return {'name': e.key, 'score': avg.round()};
    }).toList()
      ..sort((a, b) => (b['score'] as int).compareTo(a['score'] as int));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'SUBJECT PROFICIENCY',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: Color(0xFF767676),
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 12),
        if (proficiencies.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Center(
                child: Column(
                  children: const [
                    Icon(LucideIcons.barChart2,
                        size: 40, color: Color(0xFFE8E8E8)),
                    SizedBox(height: 12),
                    Text(
                      'Take some tests to see your subject proficiency',
                      style: TextStyle(color: Color(0xFF767676)),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          )
        else
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: proficiencies
                    .take(6)
                    .map((p) => _proficiencyBar(
                          p['name'] as String,
                          (p['score'] as int).toDouble(),
                        ))
                    .toList(),
              ),
            ),
          ),
      ],
    );
  }

  Widget _proficiencyBar(String name, double score) {
    Color barColor;
    if (score >= 80) {
      barColor = const Color(0xFF43B02A);
    } else if (score >= 60) {
      barColor = Colors.orange;
    } else {
      barColor = Colors.redAccent;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  name,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                '${score.round()}%',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: barColor,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: score / 100,
              backgroundColor: const Color(0xFFE8E8E8),
              color: barColor,
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }

  // ── Weekly Activity chart ──────────────────────────────────────
  Widget _buildWeeklyChart() {
    if (_weeklyStats.isEmpty) {
      return const SizedBox.shrink();
    }

    final maxMins = _weeklyStats.fold<int>(
        1, (m, s) => (s['study_minutes'] as int) > m ? s['study_minutes'] : m);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'WEEKLY ACTIVITY',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: Color(0xFF767676),
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              height: 160,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: _weeklyStats.map((day) {
                  final mins = (day['study_minutes'] ?? 0) as int;
                  final tests = (day['tests_completed'] ?? 0) as int;
                  final stars = (day['stars_earned'] ?? 0) as int;
                  final ratio = maxMins > 0 ? mins / maxMins : 0.0;

                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 3),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          if (stars > 0)
                            Text('⭐',
                                style: const TextStyle(fontSize: 10)),
                          if (tests > 0)
                            Text('$tests',
                                style: const TextStyle(
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF767676))),
                          const SizedBox(height: 4),
                          Container(
                            height: 100 * ratio,
                            decoration: BoxDecoration(
                              color: mins > 0
                                  ? const Color(0xFF43B02A)
                                  : const Color(0xFFE8E8E8),
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            day['day_name'] ?? '',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF767676),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
