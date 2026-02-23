import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator, else use the machine's current IP
  static const String _devBaseUrlWeb = 'http://localhost:8001/api/v1';
  static const String _devBaseUrlAndroid = 'http://10.0.2.2:8001/api/v1';
  static const String _devBaseUrlOther = 'http://localhost:8001/api/v1';
  static const String _prodBaseUrl = 'https://askanand-simba.up.railway.app/api/v1';

  static String get baseUrl {
    const bool isProd = bool.fromEnvironment('dart.vm.product');
    if (isProd) {
      return _prodBaseUrl;
    }
    if (kIsWeb) {
      return _devBaseUrlWeb;
    } else if (Platform.isAndroid) {
      return _devBaseUrlAndroid;
    }
    return _devBaseUrlOther;
  }

  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 120),  // 2 minutes for slow connections
    receiveTimeout: const Duration(seconds: 180),  // 3 minutes for question generation
  ));
  final _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        debugPrint('📡 API REQUEST: ${options.method} ${options.path}');
        final token = await _storage.read(key: 'token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onResponse: (response, handler) {
        debugPrint('✅ API RESPONSE: ${response.statusCode}');
        return handler.next(response);
      },
      onError: (e, handler) async {
        debugPrint('❌ API ERROR: ${e.message}');
        if (e.response?.statusCode == 401) {
          debugPrint('🔄 401 Unauthorized - Clearing invalid token and getting fresh guest token');
          
          // Clear old invalid token
          await _storage.delete(key: 'token');
          await _storage.delete(key: 'user');
          
          try {
            // Get fresh guest token
            final guestResponse = await _dio.post('/auth/guest');
            final newToken = guestResponse.data['access_token'];
            
            // Save new token
            await _storage.write(key: 'token', value: newToken);
            await _storage.write(key: 'user', value: jsonEncode(guestResponse.data['user']));
            
            debugPrint('✅ Got fresh guest token, retrying original request');
            
            // Retry original request with new token
            final options = e.requestOptions;
            options.headers['Authorization'] = 'Bearer $newToken';
            
            final response = await _dio.fetch(options);
            return handler.resolve(response);
          } catch (retryError) {
            debugPrint('❌ Failed to get guest token: $retryError');
            return handler.next(e);
          }
        }
        return handler.next(e);
      },
    ));
  }

  // Auth Methods
  Future<Response> login(String email, String password) async {
    final formData = FormData.fromMap({
      'username': email,
      'password': password,
    });
    return _dio.post('/auth/login', data: formData);
  }

  Future<Response> guestLogin() async {
    return _dio.post('/auth/guest');
  }

  // Dashboard Methods
  Future<Response> getDashboard() async {
    return _dio.get('/dashboard/');
  }

  // Leaderboard Methods
  Future<Response> get(String path) async {
    return _dio.get(path);
  }

  Future<Response> put(String path, {Map<String, dynamic>? data}) async {
    return _dio.put(path, data: data);
  }

  Future<Response> post(String path, {Map<String, dynamic>? data}) async {
    return _dio.post(path, data: data);
  }

  // Exam Methods
  Future<Response> getExams() async {
    return _dio.get('/exams/');
  }

  Future<Response> getExamDetails(int examId) async {
    return _dio.get('/exams/$examId');
  }

  Future<Response> getSubjects(int examId) async {
    return _dio.get('/exams/$examId/subjects');
  }

  Future<Response> getTopics(int examId, int subjectId) async {
    return _dio.get('/exams/$examId/subjects/$subjectId/topics');
  }

  Future<Response> updateProfile(Map<String, dynamic> data) async {
    return _dio.patch('/auth/me', data: data);
  }

  // Study Methods
  Future<Response> startSession(int topicId, int durationMins, {bool isRandomMode = false}) async {
    return _dio.post('/study/sessions', data: {
      'topic_id': topicId,
      'duration_mins': durationMins,
      if (isRandomMode) 'random_mode': true,
    });
  }

  Future<Response> completeSession(int sessionId, int actualDurationMins) async {
    return _dio.post('/study/sessions/$sessionId/complete', data: {
      'actual_duration_mins': actualDurationMins,
    });
  }

  Future<Response> getQuestionGenerationStatus(int sessionId) async {
    return _dio.get('/study/sessions/$sessionId/question-status');
  }

  // Test Methods
  Future<Response> startTest(int topicId, {int? sessionId}) async {
    return _dio.post('/mock-test/start', data: {
      'topic_id': topicId,
      if (sessionId != null) 'session_id': sessionId,
    });
  }

  Future<Response> submitTest(int testId, List<Map<String, dynamic>> responses, int totalTimeSeconds) async {
    return _dio.post('/mock-test/$testId/submit', data: {
      'responses': responses,
      'total_time_seconds': totalTimeSeconds,
    });
  }

  Future<Response> getResults(int testId) async {
    return _dio.get('/mock-test/$testId/results');
  }

  Future<Response> getTestHistory() async {
    return _dio.get('/mock-test/history/all');
  }

  // Question Rating Methods
  Future<Response> rateQuestion(int testId, int questionId, int rating, {String? feedback}) async {
    return _dio.post('/mock-test/$testId/rate', data: {
      'question_id': questionId,
      'rating': rating,
      if (feedback != null && feedback.isNotEmpty) 'feedback_text': feedback,
    });
  }

  // Utility method for consolidated rating
  Future<Map<int, dynamic>> rateMultipleQuestions(int testId, Map<int, Map<String, dynamic>> ratings) async {
    final results = <int, dynamic>{};
    for (var entry in ratings.entries) {
      try {
        final response = await rateQuestion(
          testId,
          entry.key,
          entry.value['rating'] as int,
          feedback: entry.value['feedback'] as String?,
        );
        results[entry.key] = {'success': true, 'data': response.data};
      } catch (e) {
        results[entry.key] = {'success': false, 'error': e.toString()};
      }
    }
    return results;
  }

  // Progress / Analytics Methods
  Future<Response> getWeeklyStats() async {
    return _dio.get('/dashboard/stats/weekly');
  }

  // Utility Methods
  Future<void> clearAuthCache() async {
    debugPrint('🗑️ Manually clearing auth cache');
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'user');
  }
}
