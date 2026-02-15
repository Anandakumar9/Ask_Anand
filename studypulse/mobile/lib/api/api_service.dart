import 'dart:io' show Platform;
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const _tokenKey = 'access_token';

  static String get baseUrl {
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000/api/v1';
      if (Platform.isIOS) return 'http://localhost:8000/api/v1';
    } catch (_) {}
    return 'http://localhost:8000/api/v1';
  }

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: _tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        handler.next(error);
      },
    ));
  }

  // --- Token management ---

  Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: _tokenKey);
  }

  Future<String?> getToken() async {
    return _storage.read(key: _tokenKey);
  }

  // --- Auth ---

  Future<Response> login(String username, String password) async {
    return _dio.post(
      '/auth/login',
      data: FormData.fromMap({
        'username': username,
        'password': password,
      }),
      options: Options(contentType: 'application/x-www-form-urlencoded'),
    );
  }

  Future<Response> register(String username, String email, String password) async {
    return _dio.post('/auth/register', data: {
      'username': username,
      'email': email,
      'password': password,
    });
  }

  Future<Response> guestLogin() async {
    return _dio.post('/auth/guest');
  }

  Future<Response> getMe() async {
    return _dio.get('/auth/me');
  }

  // --- Dashboard ---

  Future<Response> getDashboard() async {
    return _dio.get('/dashboard/');
  }

  // --- Exams ---

  Future<Response> getExams() async {
    return _dio.get('/exams/');
  }

  Future<Response> getExam(int examId) async {
    return _dio.get('/exams/$examId');
  }

  Future<Response> getTopics(int examId, int subjectId) async {
    return _dio.get('/exams/$examId/subjects/$subjectId/topics');
  }

  // --- Study sessions ---

  Future<Response> startStudySession(int topicId, int durationMins) async {
    return _dio.post('/study/sessions', data: {
      'topic_id': topicId,
      'duration_mins': durationMins,
    });
  }

  Future<Response> completeStudySession(int sessionId, int actualDurationMins) async {
    return _dio.post('/study/sessions/$sessionId/complete', queryParameters: {
      'actual_duration_mins': actualDurationMins,
    });
  }

  // --- Mock test ---

  Future<Response> startMockTest({
    required int topicId,
    int? sessionId,
    int questionCount = 10,
  }) async {
    return _dio.post('/mock-test/start', data: {
      'topic_id': topicId,
      if (sessionId != null) 'session_id': sessionId,
      'question_count': questionCount,
    });
  }

  Future<Response> submitMockTest(
    int testId,
    List<Map<String, dynamic>> responses,
    int totalTimeSeconds,
  ) async {
    return _dio.post('/mock-test/$testId/submit', data: {
      'responses': responses,
      'total_time_seconds': totalTimeSeconds,
    });
  }

  Future<Response> getTestResults(int testId) async {
    return _dio.get('/mock-test/$testId/results');
  }

  Future<Response> rateQuestion(int questionId, int rating, {String? feedback}) async {
    return _dio.post('/mock-test/rate-question', data: {
      'question_id': questionId,
      'rating': rating,
      if (feedback != null) 'feedback': feedback,
    });
  }

  // --- Leaderboard ---

  Future<Response> getLeaderboard() async {
    return _dio.get('/leaderboard/');
  }

  // --- Profile ---

  Future<Response> getProfileStats() async {
    return _dio.get('/profile/stats');
  }
}
