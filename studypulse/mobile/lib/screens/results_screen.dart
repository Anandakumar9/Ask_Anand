import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:confetti/confetti.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import 'package:mobile/providers/app_provider.dart';
import 'package:mobile/models/mock_test.dart';

class ResultsScreen extends StatefulWidget {
  final TestResult result;
  final List<Question> questions;

  const ResultsScreen({
    super.key,
    required this.result,
    required this.questions,
  });

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  late ConfettiController _confettiController;
  bool _showDetails = false;

  @override
  void initState() {
    super.initState();
    _confettiController =
        ConfettiController(duration: const Duration(seconds: 3));
    if (widget.result.starEarned) {
      _confettiController.play();
    }
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  void _rateQuestion(int questionId) {
    int rating = 3;
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Rate This Question'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('How was the quality of this AI-generated question?'),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (i) {
                  return IconButton(
                    icon: Icon(
                      i < rating ? Icons.star : Icons.star_border,
                      color: Colors.amber,
                      size: 32,
                    ),
                    onPressed: () =>
                        setDialogState(() => rating = i + 1),
                  );
                }),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                context
                    .read<AppProvider>()
                    .rateQuestion(questionId, rating);
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Thanks for your feedback!')),
                );
              },
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final result = widget.result;
    final scorePercent = result.score / 100;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Test Results'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context)
              .popUntil((route) => route.isFirst),
        ),
      ),
      body: Stack(
        children: [
          ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Score card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      if (result.starEarned) ...[
                        const Icon(Icons.star_rounded,
                            color: Colors.amber, size: 56),
                        const SizedBox(height: 8),
                        Text('Star Earned! ⭐',
                            style: GoogleFonts.poppins(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.amber[700])),
                        const SizedBox(height: 12),
                      ] else ...[
                        Text('Keep Practicing!',
                            style: GoogleFonts.poppins(
                                fontSize: 20, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text('Score 85% or above to earn a star',
                            style: TextStyle(color: Colors.grey[600])),
                        const SizedBox(height: 12),
                      ],
                      CircularPercentIndicator(
                        radius: 65.0,
                        lineWidth: 12.0,
                        percent: scorePercent.clamp(0.0, 1.0),
                        center: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '${result.score.toStringAsFixed(0)}%',
                              style: GoogleFonts.poppins(
                                  fontSize: 28, fontWeight: FontWeight.bold),
                            ),
                            Text('Score',
                                style: TextStyle(
                                    color: Colors.grey[600], fontSize: 12)),
                          ],
                        ),
                        progressColor: result.starEarned
                            ? Colors.amber
                            : theme.colorScheme.primary,
                        backgroundColor:
                            theme.colorScheme.surfaceContainerHighest,
                        circularStrokeCap: CircularStrokeCap.round,
                      ),
                      const SizedBox(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _ResultStat(
                            label: 'Correct',
                            value: '${result.correctAnswers}',
                            color: Colors.green,
                          ),
                          _ResultStat(
                            label: 'Wrong',
                            value:
                                '${result.totalQuestions - result.correctAnswers}',
                            color: Colors.red,
                          ),
                          _ResultStat(
                            label: 'Total',
                            value: '${result.totalQuestions}',
                            color: theme.colorScheme.primary,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Toggle details
              TextButton.icon(
                onPressed: () =>
                    setState(() => _showDetails = !_showDetails),
                icon: Icon(
                    _showDetails ? Icons.expand_less : Icons.expand_more),
                label: Text(
                    _showDetails ? 'Hide Details' : 'Show Question Details'),
              ),

              // Question details
              if (_showDetails && result.questionResults != null)
                ...result.questionResults!.asMap().entries.map((entry) {
                  final qr = entry.value;
                  final isAi = widget.questions.length > entry.key &&
                      widget.questions[entry.key].isAiGenerated;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ExpansionTile(
                      leading: CircleAvatar(
                        radius: 16,
                        backgroundColor:
                            qr.isCorrect ? Colors.green : Colors.red,
                        child: Icon(
                          qr.isCorrect ? Icons.check : Icons.close,
                          color: Colors.white,
                          size: 18,
                        ),
                      ),
                      title: Text('Q${entry.key + 1}: ${qr.questionText}',
                          maxLines: 2, overflow: TextOverflow.ellipsis),
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _AnswerRow(
                                  label: 'Your Answer',
                                  value: qr.userAnswer,
                                  isCorrect: qr.isCorrect),
                              if (!qr.isCorrect)
                                _AnswerRow(
                                    label: 'Correct Answer',
                                    value: qr.correctAnswer,
                                    isCorrect: true),
                              if (qr.explanation != null) ...[
                                const SizedBox(height: 8),
                                Text('Explanation: ${qr.explanation}',
                                    style: TextStyle(
                                        color: Colors.grey[700],
                                        fontSize: 13)),
                              ],
                              if (isAi) ...[
                                const SizedBox(height: 8),
                                OutlinedButton.icon(
                                  onPressed: () =>
                                      _rateQuestion(qr.questionId),
                                  icon: const Icon(Icons.star_outline,
                                      size: 16),
                                  label: const Text('Rate AI Question',
                                      style: TextStyle(fontSize: 12)),
                                  style: OutlinedButton.styleFrom(
                                    visualDensity: VisualDensity.compact,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }),

              const SizedBox(height: 24),

              // Actions
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton.icon(
                  onPressed: () => Navigator.of(context)
                      .popUntil((route) => route.isFirst),
                  icon: const Icon(Icons.home),
                  label: const Text('Back to Home',
                      style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),

          // Confetti
          Align(
            alignment: Alignment.topCenter,
            child: ConfettiWidget(
              confettiController: _confettiController,
              blastDirectionality: BlastDirectionality.explosive,
              shouldLoop: false,
              colors: const [
                Colors.green,
                Colors.amber,
                Colors.blue,
                Colors.pink,
                Colors.orange,
                Colors.purple,
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ResultStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _ResultStat({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: GoogleFonts.poppins(
                fontSize: 24, fontWeight: FontWeight.bold, color: color)),
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
      ],
    );
  }
}

class _AnswerRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isCorrect;

  const _AnswerRow({
    required this.label,
    required this.value,
    required this.isCorrect,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$label: ',
              style:
                  const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
          Expanded(
            child: Text(value,
                style: TextStyle(
                  color: isCorrect ? Colors.green : Colors.red,
                  fontSize: 13,
                )),
          ),
        ],
      ),
    );
  }
}
