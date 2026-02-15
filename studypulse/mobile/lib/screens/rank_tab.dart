import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mobile/providers/app_provider.dart';

class RankTab extends StatefulWidget {
  const RankTab({super.key});

  @override
  State<RankTab> createState() => _RankTabState();
}

class _RankTabState extends State<RankTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().loadLeaderboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppProvider>();
    final theme = Theme.of(context);

    if (app.leaderboardLoading && app.leaderboard.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: () => app.loadLeaderboard(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Leaderboard',
              style: GoogleFonts.poppins(
                  fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('See how you rank against others',
              style: TextStyle(color: Colors.grey[600])),
          const SizedBox(height: 20),

          if (app.leaderboard.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  children: [
                    Icon(Icons.emoji_events_outlined,
                        size: 64, color: Colors.grey[400]),
                    const SizedBox(height: 12),
                    Text('No rankings yet',
                        style:
                            TextStyle(color: Colors.grey[600], fontSize: 16)),
                    const SizedBox(height: 4),
                    Text('Complete tests to appear on the leaderboard',
                        style: TextStyle(color: Colors.grey[500])),
                  ],
                ),
              ),
            )
          else
            ...app.leaderboard.asMap().entries.map((entry) {
              final rank = entry.key + 1;
              final item = entry.value as Map<String, dynamic>;
              final isTopThree = rank <= 3;

              return Card(
                color: isTopThree
                    ? theme.colorScheme.primaryContainer.withAlpha(100)
                    : null,
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: _rankColor(rank),
                    child: Text('$rank',
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold)),
                  ),
                  title: Text(
                    item['username'] as String? ?? 'User',
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  subtitle: Text(
                    'Stars: ${item['stars'] ?? 0} · Accuracy: ${((item['accuracy'] as num?)?.toDouble() ?? 0).toStringAsFixed(0)}%',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (isTopThree)
                        Icon(Icons.emoji_events,
                            color: _rankColor(rank), size: 20),
                      const SizedBox(width: 4),
                      Text(
                        '${item['score'] ?? item['total_score'] ?? 0}',
                        style: GoogleFonts.poppins(
                            fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                ),
              );
            }),
        ],
      ),
    );
  }

  Color _rankColor(int rank) {
    switch (rank) {
      case 1:
        return const Color(0xFFFFD700);
      case 2:
        return const Color(0xFFC0C0C0);
      case 3:
        return const Color(0xFFCD7F32);
      default:
        return Colors.grey;
    }
  }
}
