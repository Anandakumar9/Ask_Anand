import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mobile/providers/app_provider.dart';
import 'package:mobile/models/mock_test.dart';
import 'package:mobile/screens/results_screen.dart';

class MockTestScreen extends StatefulWidget {
  final int topicId;
  final String topicName;

  const MockTestScreen({
    super.key,
    required this.topicId,
    required this.topicName,
  });

  @override
  State<MockTestScreen> createState() => _MockTestScreenState();
}

class _MockTestScreenState extends State<MockTestScreen> {
  bool _loading = true;
  bool _submitting = false;
  int _currentIndex = 0;
  final Map<int, String> _answers = {};
  final Stopwatch _stopwatch = Stopwatch();
  late List<Question> _questions;

  @override
  void initState() {
    super.initState();
    _loadTest();
  }

  Future<void> _loadTest() async {
    final app = context.read<AppProvider>();
    final success = await app.startMockTest();
    if (!mounted) return;

    if (success && app.currentTest != null) {
      setState(() {
        _questions = app.currentTest!.questions;
        _loading = false;
      });
      _stopwatch.start();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to load test questions')),
      );
      Navigator.pop(context);
    }
  }

  void _selectAnswer(String answer) {
    setState(() {
      _answers[_questions[_currentIndex].id] = answer;
    });
  }

  void _nextQuestion() {
    if (_currentIndex < _questions.length - 1) {
      setState(() => _currentIndex++);
    }
  }

  void _previousQuestion() {
    if (_currentIndex > 0) {
      setState(() => _currentIndex--);
    }
  }

  Future<void> _submitTest() async {
    // Confirm submission
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Submit Test?'),
        content: Text(
            'You have answered ${_answers.length} of ${_questions.length} questions. Submit now?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Review'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Submit'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _submitting = true);
    _stopwatch.stop();

    final responses = _questions.map((q) {
      return {
        'question_id': q.id,
        'answer': _answers[q.id] ?? '',
      };
    }).toList();

    final app = context.read<AppProvider>();
    final success = await app.submitMockTest(
      responses,
      _stopwatch.elapsed.inSeconds,
    );

    if (!mounted) return;

    if (success && app.lastResult != null) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ResultsScreen(
            result: app.lastResult!,
            questions: _questions,
          ),
        ),
      );
    } else {
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to submit test')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.topicName)),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text('Generating questions...',
                  style: TextStyle(color: Colors.grey[600])),
            ],
          ),
        ),
      );
    }

    if (_submitting) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text('Submitting your answers...',
                  style: TextStyle(color: Colors.grey[600])),
            ],
          ),
        ),
      );
    }

    final question = _questions[_currentIndex];
    final selectedAnswer = _answers[question.id];
    final isLast = _currentIndex == _questions.length - 1;

    return Scaffold(
      appBar: AppBar(
        title: Text('Question ${_currentIndex + 1}/${_questions.length}'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('Quit Test?'),
                content: const Text(
                    'Your progress will be lost. Are you sure?'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('Cancel'),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pop(ctx);
                      Navigator.pop(context);
                    },
                    child: const Text('Quit',
                        style: TextStyle(color: Colors.red)),
                  ),
                ],
              ),
            );
          },
        ),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Text(
                '${_answers.length}/${_questions.length} answered',
                style: TextStyle(color: Colors.grey[600], fontSize: 13),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Progress bar
          LinearProgressIndicator(
            value: (_currentIndex + 1) / _questions.length,
            backgroundColor: theme.colorScheme.surfaceContainerHighest,
          ),

          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (question.difficulty != null)
                    Chip(
                      label: Text(question.difficulty!,
                          style: const TextStyle(fontSize: 11)),
                      backgroundColor: _difficultyColor(question.difficulty!),
                      visualDensity: VisualDensity.compact,
                    ),
                  const SizedBox(height: 8),
                  Text(
                    question.questionText,
                    style: GoogleFonts.poppins(
                        fontSize: 17, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 20),
                  ...question.options.asMap().entries.map((entry) {
                    final option = entry.value;
                    final isSelected = selectedAnswer == option;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () => _selectAnswer(option),
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: isSelected
                                  ? theme.colorScheme.primary
                                  : Colors.grey[300]!,
                              width: isSelected ? 2 : 1,
                            ),
                            borderRadius: BorderRadius.circular(12),
                            color: isSelected
                                ? theme.colorScheme.primaryContainer
                                    .withAlpha(100)
                                : null,
                          ),
                          child: Row(
                            children: [
                              CircleAvatar(
                                radius: 14,
                                backgroundColor: isSelected
                                    ? theme.colorScheme.primary
                                    : Colors.grey[300],
                                child: Text(
                                  String.fromCharCode(65 + entry.key),
                                  style: TextStyle(
                                    color: isSelected
                                        ? Colors.white
                                        : Colors.grey[700],
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(option,
                                    style: const TextStyle(fontSize: 15)),
                              ),
                              if (isSelected)
                                Icon(Icons.check_circle,
                                    color: theme.colorScheme.primary,
                                    size: 20),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),

          // Navigation buttons
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withAlpha(15),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                if (_currentIndex > 0)
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _previousQuestion,
                      icon: const Icon(Icons.arrow_back),
                      label: const Text('Previous'),
                    ),
                  ),
                if (_currentIndex > 0) const SizedBox(width: 12),
                Expanded(
                  child: isLast
                      ? FilledButton.icon(
                          onPressed: _submitTest,
                          icon: const Icon(Icons.check),
                          label: const Text('Submit'),
                        )
                      : FilledButton.icon(
                          onPressed: _nextQuestion,
                          icon: const Icon(Icons.arrow_forward),
                          label: const Text('Next'),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _difficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return Colors.green[100]!;
      case 'medium':
        return Colors.orange[100]!;
      case 'hard':
        return Colors.red[100]!;
      default:
        return Colors.grey[100]!;
    }
  }
}
