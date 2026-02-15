import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/linear_percent_indicator.dart';
import 'package:mobile/providers/auth_provider.dart';
import 'package:mobile/providers/app_provider.dart';
import 'package:mobile/screens/login_screen.dart';

class ProfileTab extends StatefulWidget {
  const ProfileTab({super.key});

  @override
  State<ProfileTab> createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().loadProfileStats();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final app = context.watch<AppProvider>();
    final theme = Theme.of(context);
    final user = auth.user;
    final stats = app.profileStats;

    return RefreshIndicator(
      onRefresh: () => app.loadProfileStats(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Profile header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 40,
                    backgroundColor: theme.colorScheme.primaryContainer,
                    child: Text(
                      (user?.username.isNotEmpty == true
                              ? user!.username[0]
                              : '?')
                          .toUpperCase(),
                      style: GoogleFonts.poppins(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    user?.fullName ?? user?.username ?? 'User',
                    style: GoogleFonts.poppins(
                        fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    user?.email ?? '',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                  if (user?.isGuest == true)
                    Chip(
                      label: const Text('Guest Account'),
                      backgroundColor: Colors.orange[100],
                      labelStyle: const TextStyle(fontSize: 12),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Stats
          if (app.profileLoading && stats == null)
            const Center(child: CircularProgressIndicator())
          else ...[
            Text('Performance',
                style: GoogleFonts.poppins(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),

            _ProfileStatRow(
              icon: Icons.timer,
              label: 'Study Sessions',
              value: '${stats?['total_sessions'] ?? 0}',
            ),
            _ProfileStatRow(
              icon: Icons.star_rounded,
              label: 'Stars Earned',
              value: '${stats?['total_stars'] ?? 0}',
              valueColor: Colors.amber,
            ),
            _ProfileStatRow(
              icon: Icons.quiz,
              label: 'Tests Completed',
              value: '${stats?['tests_completed'] ?? 0}',
            ),
            _ProfileStatRow(
              icon: Icons.access_time,
              label: 'Total Study Time',
              value: '${stats?['total_study_mins'] ?? 0} mins',
            ),
            const SizedBox(height: 16),

            // Accuracy bar
            Text('Accuracy',
                style: GoogleFonts.poppins(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Overall Accuracy'),
                        Text(
                          '${((stats?['avg_accuracy'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}%',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    LinearPercentIndicator(
                      lineHeight: 10.0,
                      percent: (((stats?['avg_accuracy'] as num?)
                                      ?.toDouble() ??
                                  0) /
                              100)
                          .clamp(0.0, 1.0),
                      progressColor: theme.colorScheme.primary,
                      backgroundColor:
                          theme.colorScheme.surfaceContainerHighest,
                      barRadius: const Radius.circular(5),
                      padding: EdgeInsets.zero,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Best Score'),
                        Text(
                          '${((stats?['best_score'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}%',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    LinearPercentIndicator(
                      lineHeight: 10.0,
                      percent: (((stats?['best_score'] as num?)
                                      ?.toDouble() ??
                                  0) /
                              100)
                          .clamp(0.0, 1.0),
                      progressColor: Colors.amber,
                      backgroundColor:
                          theme.colorScheme.surfaceContainerHighest,
                      barRadius: const Radius.circular(5),
                      padding: EdgeInsets.zero,
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),

          // Logout
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () async {
                await auth.logout();
                if (context.mounted) {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                    (_) => false,
                  );
                }
              },
              icon: const Icon(Icons.logout, color: Colors.red),
              label:
                  const Text('Logout', style: TextStyle(color: Colors.red)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Colors.red),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileStatRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _ProfileStatRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 6),
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(label),
        trailing: Text(
          value,
          style: GoogleFonts.poppins(
            fontWeight: FontWeight.bold,
            fontSize: 16,
            color: valueColor,
          ),
        ),
      ),
    );
  }
}
