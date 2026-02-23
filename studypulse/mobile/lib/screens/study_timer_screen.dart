import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'dart:async';
import 'package:percent_indicator/circular_percent_indicator.dart';
import 'package:provider/provider.dart';
import '../api/api_service.dart';
import '../store/app_store.dart';
import '../store/app_theme.dart';
import 'test_screen.dart';

class StudyTimerScreen extends StatefulWidget {
  final int topicId;
  final String topicName;
  final int durationMins;
  final bool isRandomMode;

  const StudyTimerScreen({
    super.key,
    required this.topicId,
    required this.topicName,
    this.durationMins = 45,
    this.isRandomMode = false,
  });

  @override
  State<StudyTimerScreen> createState() => _StudyTimerScreenState();
}

class _StudyTimerScreenState extends State<StudyTimerScreen> {
  final _api = ApiService();
  late int _secondsRemaining;
  late int _totalSeconds;
  bool _isActive = false;
  int? _sessionId;
  Timer? _timer;
  Timer? _pollTimer;
  String? _questionStatus = 'pending';
  int? _generatedQuestionCount = 0;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _totalSeconds = widget.durationMins * 60;
    _secondsRemaining = _totalSeconds;
    _startRemoteSession();
  }

  Future<void> _startRemoteSession() async {
    try {
      debugPrint('📡 Starting session: topic=${widget.topicId}, duration=${widget.durationMins}, random=${widget.isRandomMode}');
      final response = await _api.startSession(widget.topicId, widget.durationMins, isRandomMode: widget.isRandomMode);
      
      // Backend returns 'session_id', not 'id'
      final sessionId = response.data['session_id'];
      debugPrint('✅ Session created: ID=$sessionId');
      
      setState(() {
        _sessionId = sessionId;
        _isActive = true;
        _loading = false;
      });
      _startLocalTimer();
      _startPollingQuestionStatus();
    } catch (e) {
      debugPrint('❌ Failed to start session: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error starting session: $e'),
            backgroundColor: Colors.red,
          ),
        );
        Navigator.pop(context);
      }
    }
  }

  void _startLocalTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsRemaining > 0 && _isActive) {
        setState(() {
          _secondsRemaining--;
        });
      } else if (_secondsRemaining == 0) {
        // Timer reached 0 - stop it
        setState(() => _isActive = false);
        _timer?.cancel();
      }
    });
  }

  void _startPollingQuestionStatus() {
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      if (_sessionId == null) return;

      try {
        final response = await _api.getQuestionGenerationStatus(_sessionId!);
        final status = response.data['status'] as String?;
        final questionCount = response.data['question_count'] as int?;

        if (mounted) {
          setState(() {
            _questionStatus = status ?? 'pending';
            _generatedQuestionCount = questionCount ?? 0;
          });

          // Stop polling once completed
          if (status == 'completed') {
            _pollTimer?.cancel();
            debugPrint('✅ Question generation completed: $questionCount questions');
          }
        }
      } catch (e) {
        debugPrint('⚠️ Error polling question status: $e');
        // Don't show error to user, just log it
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pollTimer?.cancel();
    super.dispose();
  }

  String _formatTime(int seconds) {
    int mins = seconds ~/ 60;
    int secs = seconds % 60;
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  Future<void> _handleEndSession() async {
    if (_sessionId == null) {
      debugPrint('❌ Cannot end session - sessionId is null');
      return;
    }
    
    setState(() => _loading = true);
    try {
      int actualMins = (_totalSeconds - _secondsRemaining) ~/ 60;
      debugPrint('📡 Completing session: id=$_sessionId, duration=$actualMins mins');
      
      // Complete session - backend returns cached questions
      final response = await _api.completeSession(_sessionId!, actualMins > 0 ? actualMins : 1);
      
      // Extract questions from response
      final questions = response.data['questions'] as List?;
      final cached = response.data['cached'] as bool? ?? false;
      
      debugPrint('✅ Session completed, got ${questions?.length ?? 0} questions (cached: $cached)');
      
      if (mounted) {
        if (questions != null && questions.isNotEmpty) {
          // Navigate to test with pre-loaded questions
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => TestScreen(
                topicId: widget.topicId,
                topicName: widget.topicName,
                sessionId: _sessionId,
                preloadedQuestions: questions,  // Pass cached questions
              ),
            ),
          );
        } else {
          // Fallback: navigate without questions (will fetch on test screen)
          debugPrint('⚠️ No questions in response, will fetch on test screen');
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => TestScreen(
                topicId: widget.topicId,
                topicName: widget.topicName,
                sessionId: _sessionId,
              ),
            ),
          );
        }
      }
    } catch (e) {
      debugPrint('❌ Error ending session: $e');
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    double progress = (_totalSeconds - _secondsRemaining) / _totalSeconds;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(widget.isRandomMode ? 'Random Mix Session' : 'Study Session'),
        actions: [
          Consumer<AppStore>(
            builder: (context, appStore, child) {
              return DarkModeToggle(
                isDarkMode: appStore.isDarkMode,
                onToggle: () => appStore.toggleDarkMode(),
              );
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: _loading 
        ? const Center(child: CircularProgressIndicator(color: Color(0xFF43B02A)))
        : Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: const Color(0xFFE8E8E8)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('STUDYING', style: TextStyle(color: Color(0xFF43B02A), fontWeight: FontWeight.bold, fontSize: 10)),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 8.0),
                        child: Text('/', style: TextStyle(color: Color(0xFFE8E8E8))),
                      ),
                      Text(widget.topicName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10)),
                    ],
                  ),
                ),
                const Spacer(),
                CircularPercentIndicator(
                  radius: 120.0,
                  lineWidth: 12.0,
                  percent: progress,
                  center: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        _formatTime(_secondsRemaining),
                        style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w900, color: Color(0xFF343538)),
                      ),
                      const Text('MINUTES LEFT', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF767676))),
                    ],
                  ),
                  circularStrokeCap: CircularStrokeCap.round,
                  backgroundColor: Colors.white,
                  progressColor: const Color(0xFF43B02A),
                  animation: true,
                  animateFromLastPercent: true,
                ),
                const Spacer(),
                // Question generation progress indicator
                if (_questionStatus != 'completed')
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    child: Card(
                      elevation: 2,
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Row(
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF43B02A)),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Generating Questions',
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    _generatedQuestionCount! > 0
                                        ? 'Generated $_generatedQuestionCount questions...'
                                        : 'Preparing your test questions...',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF767676)),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                // Show Start Mock Test button when timer reaches 0
                if (_secondsRemaining == 0)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _loading ? null : _handleEndSession,
                        icon: _loading 
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : const Icon(LucideIcons.play),
                        label: Text(_loading ? 'Starting Test...' : 'Start Mock Test'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 20),
                          backgroundColor: const Color(0xFF43B02A),
                          textStyle: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  )
                else
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FloatingActionButton(
                        heroTag: 'pause',
                        onPressed: () => setState(() => _isActive = !_isActive),
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF343538),
                        child: Icon(_isActive ? LucideIcons.pause : LucideIcons.play),
                      ),
                      const SizedBox(width: 24),
                      FloatingActionButton(
                        heroTag: 'stop',
                        onPressed: _handleEndSession,
                        backgroundColor: Colors.red.shade50,
                        foregroundColor: Colors.red,
                        elevation: 0,
                        child: const Icon(LucideIcons.square),
                      ),
                    ],
                  ),
                const SizedBox(height: 48),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(color: const Color(0xFFE8F5E3), borderRadius: BorderRadius.circular(8)),
                          child: const Icon(LucideIcons.target, color: Color(0xFF43B02A), size: 20),
                        ),
                        const SizedBox(width: 16),
                        const Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Session Goal', style: TextStyle(fontWeight: FontWeight.bold)),
                            Text('Complete study and take the test', style: TextStyle(fontSize: 12, color: Color(0xFF767676))),
                          ],
                        )
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
    );
  }
}
