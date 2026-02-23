import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../api/api_service.dart';
import 'package:confetti/confetti.dart';
import '../widgets/rate_us_dialog.dart';
import '../widgets/consolidated_question_rating.dart';

class ResultsScreen extends StatefulWidget {
  final int testId;

  const ResultsScreen({super.key, required this.testId});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  final _api = ApiService();
  Map<String, dynamic>? _results;
  bool _loading = true;
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(duration: const Duration(seconds: 3));
    _fetchResults();
  }

  Future<void> _fetchResults() async {
    try {
      final response = await _api.getResults(widget.testId);
      setState(() {
        _results = response.data;
        _loading = false;
      });
      if (_results!['star_earned'] == true) {
        _confettiController.play();
      }
      
      // Increment test counter and show rate us dialog if eligible
      await RateUsDialog.incrementTestsCompleted();
      if (mounted) {
        // Delay to avoid showing dialog immediately
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) {
            RateUsDialog.showIfEligible(context);
          }
        });
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: Color(0xFF43B02A))));
    }

    final score = (_results!['score_percentage'] as num).round();
    final starEarned = _results!['star_earned'] == true;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F7),
      appBar: AppBar(
        leading: IconButton(icon: const Icon(LucideIcons.xCircle), onPressed: () => Navigator.popUntil(context, (route) => route.isFirst)),
        title: const Text('Test Results'),
        actions: [
          IconButton(icon: const Icon(LucideIcons.share2, color: Color(0xFF43B02A)), onPressed: () {}),
        ],
      ),
      body: Stack(
        alignment: Alignment.topCenter,
        children: [
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
                  child: Column(
                    children: [
                      if (starEarned) ...[
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: const BoxDecoration(color: Color(0xFFFFF7ED), shape: BoxShape.circle),
                          child: const Icon(LucideIcons.star, color: Colors.orange, size: 48),
                        ),
                        const SizedBox(height: 16),
                        const Text('Outstanding! 🎉', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
                        const Text('You earned a star!', style: TextStyle(color: Color(0xFF43B02A), fontWeight: FontWeight.bold)),
                      ] else ...[
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: const BoxDecoration(color: Color(0xFFE8F5E3), shape: BoxShape.circle),
                          child: const Icon(LucideIcons.checkCircle, color: Color(0xFF43B02A), size: 48),
                        ),
                        const SizedBox(height: 16),
                        const Text('Test Completed', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
                        const Text('Good effort! Keep practicing.', style: TextStyle(color: Color(0xFF767676), fontWeight: FontWeight.bold)),
                      ],
                      const SizedBox(height: 32),
                      Text('$score%', style: const TextStyle(fontSize: 56, fontWeight: FontWeight.w900, color: Color(0xFF43B02A))),
                      const Text('YOUR SCORE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF767676), letterSpacing: 1)),
                      const SizedBox(height: 32),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildMiniStat(LucideIcons.checkCircle, _results!['correct_count'].toString(), 'Correct', Colors.green),
                          _buildMiniStat(LucideIcons.xCircle, _results!['incorrect_count'].toString(), 'Wrong', Colors.red),
                          _buildMiniStat(LucideIcons.clock, '${_results!['time_taken_seconds']}s', 'Time', Colors.blue),
                        ],
                      )
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              
              // Question Review Section - Show all questions with their sources
              const Text('Question Review', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ...(_results!['questions'] as List).asMap().entries.map((entry) {
                final index = entry.key;
                final question = entry.value;
                final isAI = question['source'] == 'AI';
                final isCorrect = question['is_correct'] == true;
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                color: isCorrect ? Colors.green.shade100 : Colors.red.shade100,
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  '${index + 1}',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                    color: isCorrect ? Colors.green.shade700 : Colors.red.shade700,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                question['question_text'] ?? 'Question ${index + 1}',
                                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                              decoration: BoxDecoration(
                                color: isAI ? Colors.deepPurple.shade100 : Colors.blue.shade100,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    isAI ? Icons.auto_awesome : Icons.archive,
                                    size: 10,
                                    color: isAI ? Colors.deepPurple : Colors.blue.shade700,
                                  ),
                                  const SizedBox(width: 3),
                                  Text(
                                    isAI ? 'AI' : 'PYQ',
                                    style: TextStyle(
                                      fontSize: 9,
                                      fontWeight: FontWeight.bold,
                                      color: isAI ? Colors.deepPurple : Colors.blue.shade700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 4),
                            Icon(
                              isCorrect ? Icons.check_circle : Icons.cancel,
                              color: isCorrect ? Colors.green : Colors.red,
                              size: 20,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
              
              const SizedBox(height: 24),
              
              // Consolidated Question Rating Section - Only show for AI questions
              if (_results!['questions'] != null && (_results!['questions'] as List).any((q) => q['source'] == 'AI')) ...[
                ConsolidatedQuestionRating(
                  testId: widget.testId,
                  aiQuestions: (_results!['questions'] as List)
                    .where((q) => q['source'] == 'AI')
                    .map((q) => {
                      'id': q['id'],
                      'question_text': q['question_text'] ?? '',
                    })
                    .toList(),
                ),
              ],
              
              const SizedBox(height: 24),
              const Text('Performance Insights', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _buildProgressLine('Accuracy', (_results!['accuracy'] ?? score) / 100, '${(_results!['accuracy'] ?? score).round()}%'),
                      const SizedBox(height: 20),
                      _buildProgressLine('Speed', (_results!['speed_rating'] ?? 'steady') == 'fast' || (_results!['speed_rating'] ?? 'steady') == 'lightning' ? 0.9 : 0.6, (_results!['speed_rating'] ?? 'steady').toString().toUpperCase()),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                child: const Text('Back to Dashboard'),
              ),
            ],
          ),
          ConfettiWidget(
            confettiController: _confettiController,
            blastDirectionality: BlastDirectionality.explosive,
            shouldLoop: false,
            colors: const [Color(0xFF43B02A), Colors.orange, Colors.white],
          ),
        ],
      ),
    );
  }

  Widget _buildMiniStat(IconData icon, String val, String label, Color color) {
    return Column(
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(height: 4),
        Text(val, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 10, color: Color(0xFF767676))),
      ],
    );
  }

  Widget _buildProgressLine(String label, double val, String trailing) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF767676))),
            Text(trailing, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF43B02A))),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(value: val, color: const Color(0xFF43B02A), backgroundColor: const Color(0xFFE8E8E8), minHeight: 8, borderRadius: BorderRadius.circular(4)),
      ],
    );
  }
}
