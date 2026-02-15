import 'package:flutter/material.dart';
import 'package:mobile/api/api_service.dart';
import 'package:mobile/models/user.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  User? _user;
  bool _isLoading = false;
  String? _error;

  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isLoggedIn => _user != null;
  String? get error => _error;
  ApiService get api => _api;

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.login(username, password);
      final data = response.data as Map<String, dynamic>;
      await _api.saveToken(data['access_token'] as String);
      _user = User.fromJson(data['user'] as Map<String, dynamic>);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = _parseError(e);
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register(String username, String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.register(username, email, password);
      final data = response.data as Map<String, dynamic>;
      await _api.saveToken(data['access_token'] as String);
      _user = User.fromJson(data['user'] as Map<String, dynamic>);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = _parseError(e);
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> guestLogin() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final response = await _api.guestLogin();
      final data = response.data as Map<String, dynamic>;
      await _api.saveToken(data['access_token'] as String);
      _user = User.fromJson(data['user'] as Map<String, dynamic>);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = _parseError(e);
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> tryAutoLogin() async {
    final token = await _api.getToken();
    if (token == null) return false;
    try {
      final response = await _api.getMe();
      _user = User.fromJson(response.data as Map<String, dynamic>);
      notifyListeners();
      return true;
    } catch (_) {
      await _api.clearToken();
      return false;
    }
  }

  Future<void> logout() async {
    await _api.clearToken();
    _user = null;
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  String _parseError(dynamic e) {
    if (e is Exception) {
      final msg = e.toString();
      if (msg.contains('detail')) {
        final regex = RegExp(r'"detail"\s*:\s*"([^"]+)"');
        final match = regex.firstMatch(msg);
        if (match != null) return match.group(1)!;
      }
    }
    return 'Something went wrong. Please try again.';
  }
}
