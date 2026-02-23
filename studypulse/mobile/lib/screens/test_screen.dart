import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../api/api_service.dart';
import 'results_screen.dart';
import 'dart:async';
import 'package:flutter/foundation.dart'; // For debugPrint

class TestScreen extends StatefulWidget {
  final int topicId;
  final String topicName;
  final int? sessionId;
  final List? preloadedQuestions;  // Cached questions from session completion

  const TestScreen({
    super.key,
    required this.topicId,
    required this.topicName,
    this.sessionId,
    this.preloadedQuestions,  // Optional preloaded questions
  });

  @override
  State<TestScreen> createState() => _TestScreenState();
}

class _TestScreenState extends State<TestScreen> {
  final _api = ApiService();
  List _questions = [];
  int _currentIdx = 0;
  final Map<int, String> _answers = {};
  bool _loading = true;
  int? _testId;
  int _timeTakenSeconds = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initializeTest();
  }

  Future<void> _initializeTest() async {
    // If we have preloaded questions, still need to create test record
    if (widget.preloadedQuestions != null && widget.preloadedQuestions!.isNotEmpty) {
      debugPrint('✅ Have ${widget.preloadedQuestions!.length} preloaded questions');
      try {
        // Create test record with preloaded questions
        final response = await _api.startTest(widget.topicId, sessionId: widget.sessionId);
        debugPrint('✅ Test record created: ${response.data["test_id"]}');
        
        setState(() {
          _questions = widget.preloadedQuestions!;  // Use cached questions
          _testId = response.data['test_id'];  // Use proper test ID
          _loading = false;
        });
        _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
          setState(() => _timeTakenSeconds++);
        });
      } catch (e) {
        debugPrint('❌ Error creating test record: $e');
        if (mounted) Navigator.pop(context);
      }
    } else {
      // Fallback: fetch questions from API
      debugPrint('⚠️ No preloaded questions, fetching from API...');
      await _startTest();
    }
  }

  Future<void> _startTest() async {
    try {
      final response = await _api.startTest(widget.topicId, sessionId: widget.sessionId);
      setState(() {
        _questions = response.data['questions'];
        _testId = response.data['test_id'];
        _loading = false;
      });
      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() => _timeTakenSeconds++);
      });
    } catch (e) {
      debugPrint('❌ Error starting test: $e');
      if (mounted) {
        // Show error dialog instead of just popping
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('No Questions Available'),
            content: const Text(
              'This topic doesn\'t have any questions yet. '
              'Please try a different topic or contact support.',
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context); // Close dialog
                  Navigator.pop(context); // Go back to topic selection
                },
                child: const Text('Go Back'),
              ),
            ],
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String _formatTime(int seconds) {
    int mins = seconds ~/ 60;
    int secs = seconds % 60;
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  Widget _buildQuestionImages(dynamic questionImages) {
    if (questionImages == null || (questionImages as List).isEmpty) {
      return const SizedBox.shrink();
    }

    final images = questionImages as List;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        ...images.map<Widget>((imgUrl) {
          final url = imgUrl.toString();
          if (url.startsWith('data:image')) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.memory(
                  Uri.parse(url).data!.contentAsBytes(),
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.broken_image, color: Colors.grey),
                          SizedBox(width: 8),
                          Text('Image could not be loaded'),
                        ],
                      ),
                    );
                  },
                ),
              ),
            );
          } else {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  url,
                  fit: BoxFit.contain,
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) return child;
                    return Container(
                      height: 200,
                      color: Colors.grey[100],
                      child: Center(
                        child: CircularProgressIndicator(
                          value: loadingProgress.expectedTotalBytes != null
                              ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                              : null,
                        ),
                      ),
                    );
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.broken_image, color: Colors.grey),
                          SizedBox(width: 8),
                          Text('Image could not be loaded'),
                        ],
                      ),
                    );
                  },
                ),
              ),
            );
          }
        }).toList(),
      ],
    );
  }

  Future<void> _handleSubmit() async {
    setState(() => _loading = true);
    try {
      final responses = _questions.map((q) => {
        'question_id': q['id'],
        'answer': _answers[q['id']],
        'time_spent_seconds': 0,
      }).toList();

      await _api.submitTest(_testId!, responses, _timeTakenSeconds);
      
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => ResultsScreen(testId: _testId!),
          ),
        );
      }
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: Color(0xFF43B02A))));
    }

    // Check if questions list is empty
    if (_questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                const Text(
                  'No questions available',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Questions could not be loaded. Please try again.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Go Back'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final question = _questions[_currentIdx];
    final options = question['options'] as Map<String, dynamic>;
    final selectedOption = _answers[question['id']];
    final progress = (_currentIdx + 1) / _questions.length;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F7),
      appBar: AppBar(
        title: Text('Question ${_currentIdx + 1} of ${_questions.length}'),
        actions: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFF7F7F7),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFE8E8E8)),
            ),
            child: Row(
              children: [
                const Icon(LucideIcons.clock, size: 14),
                const SizedBox(width: 4),
                Text(_formatTime(_timeTakenSeconds), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              ],
            ),
          )
        ],
      ),
      body: Column(
        children: [
          LinearProgressIndicator(value: progress, color: const Color(0xFF43B02A), backgroundColor: const Color(0xFFE8E8E8)),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: const Color(0xFF43B02A), borderRadius: BorderRadius.circular(4)),
                          child: Text(
                            question['source'] == 'AI' ? 'AI QUESTION' : 'PREVIOUS YEAR',
                            style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold, letterSpacing: 1),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          question['question_text'],
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, height: 1.4),
                        ),
                        const SizedBox(height: 16),
                        _buildQuestionImages(question['question_images']),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                ...options.entries.map((entry) {
                  final isSelected = selectedOption == entry.key;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12.0),
                    child: GestureDetector(
                      onTap: () => setState(() => _answers[question['id']] = entry.key),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: isSelected ? const Color(0xFF43B02A) : const Color(0xFFE8E8E8), width: 2),
                          boxShadow: isSelected ? [BoxShadow(color: const Color(0xFF43B02A).withOpacity(0.1), blurRadius: 8)] : null,
                        ),
                        child: Row(
                          children: [
                            Container(
                              height: 24, width: 24,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isSelected ? const Color(0xFF43B02A) : Colors.transparent,
                                border: Border.all(color: isSelected ? const Color(0xFF43B02A) : const Color(0xFFE8E8E8), width: 2),
                              ),
                              child: isSelected ? const Icon(Icons.check, size: 14, color: Colors.white) : Center(child: Text(entry.key, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold))),
                            ),
                            const SizedBox(width: 16),
                            Expanded(child: Text(entry.value, style: const TextStyle(fontWeight: FontWeight.w600))),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                   OutlinedButton(
                    onPressed: _currentIdx > 0 ? () => setState(() => _currentIdx--) : null,
                    style: OutlinedButton.styleFrom(minimumSize: const Size(100, 56)),
                    child: const Text('Back'),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _currentIdx == _questions.length - 1 ? _handleSubmit : () => setState(() => _currentIdx++),
                      child: Text(_currentIdx == _questions.length - 1 ? 'Submit Test' : 'Next Question'),
                    ),
                  ),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
