import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../api/api_service.dart';
import 'results_screen.dart';

class ResultsHistoryScreen extends StatefulWidget {
  const ResultsHistoryScreen({super.key});

  @override
  State<ResultsHistoryScreen> createState() => _ResultsHistoryScreenState();
}

class _ResultsHistoryScreenState extends State<ResultsHistoryScreen> with SingleTickerProviderStateMixin {
  final _api = ApiService();
  List _allResults = [];
  Map<String, List> _topicWiseResults = {};
  bool _loading = true;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchResults();
  }

  Future<void> _fetchResults() async {
    setState(() => _loading = true);
    try {
      final response = await _api.getTestHistory();
      final List results = response.data is List ? response.data : [];

      setState(() {
        _allResults = results;

        // Group by topic
        _topicWiseResults = {};
        for (var result in _allResults) {
          final topicName = (result['topic_name'] ?? 'Unknown Topic') as String;
          if (!_topicWiseResults.containsKey(topicName)) {
            _topicWiseResults[topicName] = [];
          }
          _topicWiseResults[topicName]!.add(result);
        }

        _loading = false;
      });
    } catch (e) {
      debugPrint('Failed to fetch test history: $e');
      setState(() {
        _allResults = [];
        _topicWiseResults = {};
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F7),
      appBar: AppBar(
        title: const Text('Test Results'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF43B02A),
          unselectedLabelColor: const Color(0xFF767676),
          indicatorColor: const Color(0xFF43B02A),
          tabs: const [
            Tab(text: 'All Tests'),
            Tab(text: 'By Topic'),
          ],
        ),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF43B02A)),
            )
          : TabBarView(
              controller: _tabController,
              children: [
                _buildAllTestsTab(),
                _buildTopicWiseTab(),
              ],
            ),
    );
  }

  Widget _buildAllTestsTab() {
    if (_allResults.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              LucideIcons.fileText,
              size: 64,
              color: Color(0xFFE8E8E8),
            ),
            const SizedBox(height: 16),
            const Text(
              'No test results yet',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF767676),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Take your first test to see results here',
              style: TextStyle(color: Color(0xFF767676)),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _allResults.length,
      itemBuilder: (context, index) {
        final result = _allResults[index];
        return _buildResultCard(result);
      },
    );
  }

  Widget _buildTopicWiseTab() {
    if (_topicWiseResults.isEmpty) {
      return const Center(
        child: Text('No topic-wise results yet'),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _topicWiseResults.keys.length,
      itemBuilder: (context, index) {
        final topicName = _topicWiseResults.keys.elementAt(index);
        final results = _topicWiseResults[topicName]!;
        final avgScore = results.fold<double>(
              0,
              (sum, r) => sum + (r['score_percentage'] as num).toDouble(),
            ) /
            results.length;
        final totalStars = results.where((r) => r['star_earned'] == true).length;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ExpansionTile(
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F5E3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                LucideIcons.bookOpen,
                color: Color(0xFF43B02A),
                size: 20,
              ),
            ),
            title: Text(
              topicName,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            subtitle: Row(
              children: [
                Text(
                  '${results.length} tests',
                  style: const TextStyle(fontSize: 12),
                ),
                const SizedBox(width: 8),
                const Text('•', style: TextStyle(fontSize: 12)),
                const SizedBox(width: 8),
                Text(
                  'Avg: ${avgScore.round()}%',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF43B02A),
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                if (totalStars > 0) ...[
                  const Text('•', style: TextStyle(fontSize: 12)),
                  const SizedBox(width: 8),
                  const Icon(LucideIcons.star, size: 12, color: Colors.orange),
                  const SizedBox(width: 2),
                  Text(
                    '$totalStars',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ],
            ),
            children: results
                .map((result) => _buildResultCard(result, compact: true))
                .toList(),
          ),
        );
      },
    );
  }

  Widget _buildResultCard(Map<String, dynamic> result, {bool compact = false}) {
    final score = (result['score_percentage'] as num).round();
    final starEarned = result['star_earned'] as bool;
    final timeTaken = result['time_taken_seconds'] as int;
    final completedAt = DateTime.parse(result['completed_at'] as String);
    final timeAgo = _getTimeAgo(completedAt);

    return Card(
      margin: compact
          ? const EdgeInsets.symmetric(horizontal: 12, vertical: 4)
          : const EdgeInsets.only(bottom: 12),
      elevation: compact ? 0 : 2,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ResultsScreen(testId: result['id']),
            ),
          );
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Score Circle
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _getScoreColor(score).withOpacity(0.1),
                  border: Border.all(
                    color: _getScoreColor(score),
                    width: 3,
                  ),
                ),
                child: Center(
                  child: Text(
                    '$score%',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: _getScoreColor(score),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),

              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            result['topic_name'],
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (starEarned)
                          const Icon(
                            LucideIcons.star,
                            color: Colors.orange,
                            size: 20,
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      result['subject_name'],
                      style: const TextStyle(
                        color: Color(0xFF767676),
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(
                          LucideIcons.checkCircle,
                          size: 12,
                          color: Color(0xFF767676),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${result['correct_count']}/${result['total_questions']}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF767676),
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Icon(
                          LucideIcons.clock,
                          size: 12,
                          color: Color(0xFF767676),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${(timeTaken / 60).round()} min',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF767676),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          timeAgo,
                          style: const TextStyle(
                            fontSize: 11,
                            color: Color(0xFF767676),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 85) return const Color(0xFF43B02A);
    if (score >= 70) return Colors.orange;
    return Colors.red;
  }

  String _getTimeAgo(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }
}
