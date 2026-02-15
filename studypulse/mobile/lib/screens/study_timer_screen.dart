import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mobile/providers/app_provider.dart';
import 'package:mobile/screens/mock_test_screen.dart';

class StudyTimerScreen extends StatefulWidget {
  final int topicId;
  final String topicName;

  const StudyTimerScreen({
    super.key,
    required this.topicId,
    required this.topicName,
  });

  @override
  State<StudyTimerScreen> createState() => _StudyTimerScreenState();
}

class _StudyTimerScreenState extends State<StudyTimerScreen> {
  static const _durations = [5, 10, 15, 20, 30, 45, 60, 90, 120];
  int _selectedDuration = 15;
  bool _isRunning = false;
  bool _isStarting = false;
  int _remainingSeconds = 0;
  Timer? _timer;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _startSession() async {
    setState(() => _isStarting = true);
    final app = context.read<AppProvider>();
    final success = await app.startStudySession(
        widget.topicId, _selectedDuration, widget.topicName);

    if (!mounted) return;
    if (success) {
      setState(() {
        _isRunning = true;
        _isStarting = false;
        _remainingSeconds = _selectedDuration * 60;
      });
      _startTimer();
    } else {
      setState(() => _isStarting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to start session')),
      );
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_remainingSeconds <= 0) {
        timer.cancel();
        _onSessionComplete();
        return;
      }
      setState(() => _remainingSeconds--);
    });
  }

  Future<void> _onSessionComplete() async {
    final app = context.read<AppProvider>();
    final actualMins =
        ((_selectedDuration * 60 - _remainingSeconds) / 60).ceil();
    await app.completeStudySession(actualMins.clamp(1, _selectedDuration));

    if (!mounted) return;
    _showTestDialog();
  }

  void _endEarly() {
    _timer?.cancel();
    _onSessionComplete();
  }

  void _showTestDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Study Session Complete! 🎉'),
        content: const Text(
            'Great job studying! Ready to test your knowledge with a mock test?'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop();
            },
            child: const Text('Skip Test'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(
                  builder: (_) => MockTestScreen(
                    topicId: widget.topicId,
                    topicName: widget.topicName,
                  ),
                ),
              );
            },
            child: const Text('Take Test'),
          ),
        ],
      ),
    );
  }

  String _formatTime(int seconds) {
    final mins = seconds ~/ 60;
    final secs = seconds % 60;
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final progress = _isRunning
        ? 1.0 - (_remainingSeconds / (_selectedDuration * 60))
        : 0.0;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.topicName),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            if (_isRunning) {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('End Session?'),
                  content: const Text(
                      'Are you sure you want to end your study session early?'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Cancel'),
                    ),
                    FilledButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        _endEarly();
                      },
                      child: const Text('End Session'),
                    ),
                  ],
                ),
              );
            } else {
              Navigator.pop(context);
            }
          },
        ),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (!_isRunning) ...[
                Icon(Icons.timer_outlined,
                    size: 64, color: theme.colorScheme.primary),
                const SizedBox(height: 16),
                Text('Set Study Duration',
                    style: GoogleFonts.poppins(
                        fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('How long do you want to study?',
                    style: TextStyle(color: Colors.grey[600])),
                const SizedBox(height: 24),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  alignment: WrapAlignment.center,
                  children: _durations.map((d) {
                    final isSelected = d == _selectedDuration;
                    return ChoiceChip(
                      label: Text('$d min'),
                      selected: isSelected,
                      onSelected: (_) =>
                          setState(() => _selectedDuration = d),
                      selectedColor: theme.colorScheme.primaryContainer,
                    );
                  }).toList(),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: 200,
                  height: 48,
                  child: FilledButton.icon(
                    onPressed: _isStarting ? null : _startSession,
                    icon: _isStarting
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.play_arrow),
                    label: Text(_isStarting ? 'Starting...' : 'Start Studying',
                        style: const TextStyle(fontSize: 16)),
                  ),
                ),
              ] else ...[
                // Timer display
                SizedBox(
                  width: 220,
                  height: 220,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 220,
                        height: 220,
                        child: CircularProgressIndicator(
                          value: progress,
                          strokeWidth: 12,
                          backgroundColor:
                              theme.colorScheme.surfaceContainerHighest,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            _formatTime(_remainingSeconds),
                            style: GoogleFonts.poppins(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                          Text('remaining',
                              style: TextStyle(color: Colors.grey[600])),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Text('Keep studying! 📚',
                    style: GoogleFonts.poppins(
                        fontSize: 18, fontWeight: FontWeight.w500)),
                const SizedBox(height: 8),
                Text(widget.topicName,
                    style: TextStyle(color: Colors.grey[600])),
                const SizedBox(height: 32),
                OutlinedButton.icon(
                  onPressed: _endEarly,
                  icon: const Icon(Icons.stop),
                  label: const Text('End Session Early'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.orange,
                    side: const BorderSide(color: Colors.orange),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
