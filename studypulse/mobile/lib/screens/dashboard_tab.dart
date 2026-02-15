import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import 'package:mobile/providers/app_provider.dart';

class DashboardTab extends StatefulWidget {
  const DashboardTab({super.key});

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().loadDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppProvider>();
    final data = app.dashboardData;
    final theme = Theme.of(context);

    if (app.dashboardLoading && data == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final stats = data?['stats'] as Map<String, dynamic>? ?? {};
    final continueTopic = data?['continue_topic'] as Map<String, dynamic>?;
    final recentActivity = data?['recent_activity'] as List<dynamic>? ?? [];

    return RefreshIndicator(
      onRefresh: () => app.loadDashboard(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Dashboard',
              style: GoogleFonts.poppins(
                  fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),

          // Stats cards
          Row(
            children: [
              _StatCard(
                title: 'Sessions',
                value: '${stats['total_sessions'] ?? 0}',
                icon: Icons.timer_outlined,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(width: 12),
              _StatCard(
                title: 'Stars',
                value: '${stats['total_stars'] ?? 0}',
                icon: Icons.star_rounded,
                color: Colors.amber,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _StatCard(
                title: 'Tests',
                value: '${stats['tests_taken'] ?? 0}',
                icon: Icons.quiz_outlined,
                color: Colors.blue,
              ),
              const SizedBox(width: 12),
              _StatCard(
                title: 'Accuracy',
                value: '${((stats['avg_accuracy'] as num?)?.toDouble() ?? 0).toStringAsFixed(0)}%',
                icon: Icons.check_circle_outline,
                color: Colors.teal,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Accuracy gauge
          if (stats['avg_accuracy'] != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text('Overall Accuracy',
                        style: GoogleFonts.poppins(
                            fontSize: 16, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 16),
                    CircularPercentIndicator(
                      radius: 60.0,
                      lineWidth: 10.0,
                      percent: ((stats['avg_accuracy'] as num?)
                                  ?.toDouble() ??
                              0) /
                          100,
                      center: Text(
                        '${((stats['avg_accuracy'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}%',
                        style: GoogleFonts.poppins(
                            fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      progressColor: theme.colorScheme.primary,
                      backgroundColor: theme.colorScheme.surfaceContainerHighest,
                      circularStrokeCap: CircularStrokeCap.round,
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 24),

          // Continue studying
          if (continueTopic != null) ...[
            Text('Continue Studying',
                style: GoogleFonts.poppins(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Icon(Icons.play_arrow,
                      color: theme.colorScheme.primary),
                ),
                title: Text(continueTopic['topic_name'] as String? ?? 'Topic'),
                subtitle: Text(
                    continueTopic['subject_name'] as String? ?? ''),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // Recent activity
          Text('Recent Activity',
              style: GoogleFonts.poppins(
                  fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          if (recentActivity.isEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Center(
                  child: Text('No recent activity yet',
                      style: TextStyle(color: Colors.grey[600])),
                ),
              ),
            )
          else
            ...recentActivity.take(5).map((activity) {
              final a = activity as Map<String, dynamic>;
              return Card(
                child: ListTile(
                  leading: Icon(
                    a['type'] == 'study'
                        ? Icons.menu_book
                        : Icons.quiz,
                    color: theme.colorScheme.primary,
                  ),
                  title: Text(a['title'] as String? ?? ''),
                  subtitle: Text(a['subtitle'] as String? ?? ''),
                  trailing: a['score'] != null
                      ? Chip(label: Text('${a['score']}%'))
                      : null,
                ),
              );
            }),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 8),
              Text(value,
                  style: GoogleFonts.poppins(
                      fontSize: 22, fontWeight: FontWeight.bold)),
              Text(title,
                  style: TextStyle(color: Colors.grey[600], fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}
