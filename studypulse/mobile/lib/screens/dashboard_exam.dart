import 'package:flutter/material.dart';
import 'package:mobile/api/api_service.dart';
import 'package:mobile/screens/study_screen.dart';
import 'package:provider/provider.dart';
import 'package:mobile/store/app_store.dart';
import 'package:mobile/store/app_theme.dart';

class DashboardExam extends StatefulWidget {
  const DashboardExam({Key? key}) : super(key: key);

  @override
  State<DashboardExam> createState() => _DashboardExamState();
}

class _DashboardExamState extends State<DashboardExam> {
  final _api = ApiService();
  Map<String, dynamic>? _dashboardData;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() => _loading = true);
    try {
      final response = await _api.getDashboard();
      setState(() {
        _dashboardData = response.data;
        _loading = false;
      });
    } catch (e) {
      debugPrint('Dashboard error: $e');
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: const Color(0xFF6366F1),
              child: const Text(
                'S',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _dashboardData?['greeting'] ?? 'Good Morning',
                    style: const TextStyle(fontSize: 14, color: Color(0xFF6B7280)),
                  ),
                  Text(
                    (_dashboardData?['user_name'] ?? 'Scholar') + '! 👋',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1F2937),
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.notifications_outlined, color: Color(0xFF6B7280)),
              onPressed: () {},
            ),
            Consumer<AppStore>(
              builder: (context, appStore, child) {
                return DarkModeToggle(
                  isDarkMode: appStore.isDarkMode,
                  onToggle: () => appStore.toggleDarkMode(),
                );
              },
            ),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboard,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildPracticeCard(),
                    const SizedBox(height: 24),
                    _buildStatsCards(),
                    const SizedBox(height: 24),
                    _buildPerformanceGoal(),
                    const SizedBox(height: 24),
                    _buildRecentActivity(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildPracticeCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF6366F1).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Ready to practice?',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 8),
          const Text(
            'Continue your preparation for UPSC Civil Services.',
            style: TextStyle(fontSize: 14, color: Colors.white70),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const StudyScreen()),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: const Color(0xFF6366F1),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.book_outlined, size: 20),
                  SizedBox(width: 8),
                  Text('Start Now', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCards() {
    final stats = _dashboardData?['stats'] ?? {};
    return Row(
      children: [
        Expanded(child: _buildStatCard(Icons.schedule_rounded, 'SESSIONS', '${stats['sessions'] ?? 0}', const Color(0xFF3B82F6))),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard(Icons.assignment_outlined, 'TESTS', '${stats['tests'] ?? 0}', const Color(0xFF8B5CF6))),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard(Icons.star_rounded, 'STARS', '${stats['stars'] ?? 0}', const Color(0xFFFBBF24))),
      ],
    );
  }

  Widget _buildStatCard(IconData icon, String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, size: 28, color: color),
          const SizedBox(height: 8),
          Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Widget _buildPerformanceGoal() {
    final goal = _dashboardData?['performance_goal'] ?? {};
    final percentage = (goal['percentage'] ?? 0).toInt();
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.emoji_events, color: Color(0xFF6366F1), size: 20),
              const SizedBox(width: 8),
              const Text('Performance Goal', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const Spacer(),
              Text('$percentage%', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF6366F1))),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: percentage / 100,
              minHeight: 8,
              backgroundColor: const Color(0xFFE5E7EB),
              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6366F1)),
            ),
          ),
          const SizedBox(height: 8),
          const Text('General Studies I', style: TextStyle(fontSize: 13, color: Color(0xFF6B7280))),
        ],
      ),
    );
  }

  Widget _buildRecentActivity() {
    final activities = _dashboardData?['recent_activity'] ?? [];
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: const [
            Icon(Icons.history, color: Color(0xFF6B7280), size: 20),
            SizedBox(width: 8),
            Text('Recent Activity', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 12),
        if (activities.isEmpty)
          Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
            child: Center(
              child: Column(
                children: const [
                  Icon(Icons.inbox_outlined, size: 48, color: Color(0xFFD1D5DB)),
                  SizedBox(height: 12),
                  Text('No activity yet', style: TextStyle(color: Color(0xFF9CA3AF))),
                ],
              ),
            ),
          )
        else
          ...activities.map((a) => _buildActivityItem(a)).toList(),
      ],
    );
  }

  Widget _buildActivityItem(Map<String, dynamic> activity) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: const Color(0xFFEEF2FF), borderRadius: BorderRadius.circular(8)),
            child: const Icon(Icons.assignment_outlined, color: Color(0xFF6366F1), size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(activity['topic_name'] ?? 'Unknown', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text('Recently', style: const TextStyle(fontSize: 12, color: Color(0xFF9CA3AF))),
              ],
            ),
          ),
          Text('${activity['percentage'] ?? 0}%', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF6366F1))),
        ],
      ),
    );
  }
}
