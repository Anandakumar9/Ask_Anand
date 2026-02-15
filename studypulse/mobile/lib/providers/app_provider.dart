import 'package:flutter/material.dart';
import 'package:mobile/api/api_service.dart';
import 'package:mobile/models/exam.dart';
import 'package:mobile/models/mock_test.dart';

class AppProvider extends ChangeNotifier {
  final ApiService _api;

  AppProvider(this._api);

  // Dashboard
  Map<String, dynamic>? _dashboardData;
  bool _dashboardLoading = false;

  Map<String, dynamic>? get dashboardData => _dashboardData;
  bool get dashboardLoading => _dashboardLoading;

  // Exams
  List<Exam> _exams = [];
  bool _examsLoading = false;

  List<Exam> get exams => _exams;
  bool get examsLoading => _examsLoading;

  // Current study session
  int? _currentSessionId;
  int? _currentTopicId;
  String? _currentTopicName;

  int? get currentSessionId => _currentSessionId;
  int? get currentTopicId => _currentTopicId;
  String? get currentTopicName => _currentTopicName;

  // Mock test
  MockTest? _currentTest;
  TestResult? _lastResult;

  MockTest? get currentTest => _currentTest;
  TestResult? get lastResult => _lastResult;

  // Leaderboard
  List<dynamic> _leaderboard = [];
  bool _leaderboardLoading = false;

  List<dynamic> get leaderboard => _leaderboard;
  bool get leaderboardLoading => _leaderboardLoading;

  // Profile stats
  Map<String, dynamic>? _profileStats;
  bool _profileLoading = false;

  Map<String, dynamic>? get profileStats => _profileStats;
  bool get profileLoading => _profileLoading;

  // --- Dashboard ---

  Future<void> loadDashboard() async {
    _dashboardLoading = true;
    notifyListeners();
    try {
      final response = await _api.getDashboard();
      _dashboardData = response.data as Map<String, dynamic>;
    } catch (_) {}
    _dashboardLoading = false;
    notifyListeners();
  }

  // --- Exams ---

  Future<void> loadExams() async {
    _examsLoading = true;
    notifyListeners();
    try {
      final response = await _api.getExams();
      final data = response.data;
      if (data is List) {
        _exams = data
            .map((e) => Exam.fromJson(e as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {}
    _examsLoading = false;
    notifyListeners();
  }

  Future<Exam?> loadExamDetail(int examId) async {
    try {
      final response = await _api.getExam(examId);
      return Exam.fromJson(response.data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<List<Topic>> loadTopics(int examId, int subjectId) async {
    try {
      final response = await _api.getTopics(examId, subjectId);
      final data = response.data;
      if (data is List) {
        return data
            .map((t) => Topic.fromJson(t as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {}
    return [];
  }

  // --- Study session ---

  Future<bool> startStudySession(int topicId, int durationMins, String topicName) async {
    try {
      final response = await _api.startStudySession(topicId, durationMins);
      final data = response.data as Map<String, dynamic>;
      _currentSessionId = data['id'] as int;
      _currentTopicId = topicId;
      _currentTopicName = topicName;
      notifyListeners();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> completeStudySession(int actualDurationMins) async {
    if (_currentSessionId == null) return;
    try {
      await _api.completeStudySession(_currentSessionId!, actualDurationMins);
    } catch (_) {}
  }

  // --- Mock test ---

  Future<bool> startMockTest({int questionCount = 10}) async {
    if (_currentTopicId == null) return false;
    try {
      final response = await _api.startMockTest(
        topicId: _currentTopicId!,
        sessionId: _currentSessionId,
        questionCount: questionCount,
      );
      _currentTest = MockTest.fromJson(response.data as Map<String, dynamic>);
      notifyListeners();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> submitMockTest(
    List<Map<String, dynamic>> responses,
    int totalTimeSeconds,
  ) async {
    if (_currentTest == null) return false;
    try {
      final response = await _api.submitMockTest(
        _currentTest!.id,
        responses,
        totalTimeSeconds,
      );
      _lastResult = TestResult.fromJson(response.data as Map<String, dynamic>);
      notifyListeners();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<TestResult?> getTestResults(int testId) async {
    try {
      final response = await _api.getTestResults(testId);
      return TestResult.fromJson(response.data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> rateQuestion(int questionId, int rating, {String? feedback}) async {
    try {
      await _api.rateQuestion(questionId, rating, feedback: feedback);
    } catch (_) {}
  }

  // --- Leaderboard ---

  Future<void> loadLeaderboard() async {
    _leaderboardLoading = true;
    notifyListeners();
    try {
      final response = await _api.getLeaderboard();
      final data = response.data;
      if (data is List) {
        _leaderboard = data;
      } else if (data is Map && data.containsKey('rankings')) {
        _leaderboard = data['rankings'] as List<dynamic>;
      }
    } catch (_) {}
    _leaderboardLoading = false;
    notifyListeners();
  }

  // --- Profile ---

  Future<void> loadProfileStats() async {
    _profileLoading = true;
    notifyListeners();
    try {
      final response = await _api.getProfileStats();
      _profileStats = response.data as Map<String, dynamic>;
    } catch (_) {}
    _profileLoading = false;
    notifyListeners();
  }

  void clearSession() {
    _currentSessionId = null;
    _currentTopicId = null;
    _currentTopicName = null;
    _currentTest = null;
    _lastResult = null;
    notifyListeners();
  }
}
