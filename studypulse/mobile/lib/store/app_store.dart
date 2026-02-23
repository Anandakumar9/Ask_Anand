import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';

class AppStore extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();
  
  String? _token;
  Map<String, dynamic>? _user;
  bool _isInitialized = false;
  bool _isDarkMode = false;

  String? get token => _token;
  Map<String, dynamic>? get user => _user;
  bool get isInitialized => _isInitialized;
  bool get isDarkMode => _isDarkMode;

  ThemeMode get themeMode => _isDarkMode ? ThemeMode.dark : ThemeMode.light;

  AppStore() {
    _initialize();
  }

  Future<void> _initialize() async {
    _token = await _storage.read(key: 'token');
    final userData = await _storage.read(key: 'user');
    if (userData != null) {
      _user = json.decode(userData);
    }
    
    // Load dark mode preference
    final darkModeData = await _storage.read(key: 'dark_mode');
    _isDarkMode = darkModeData == 'true';
    
    // Clear invalid legacy tokens (e.g., 'guest-token' string)
    if (_token != null && !_token!.contains('.')) {
      debugPrint('⚠️ Clearing invalid token format');
      await logout();
    }
    
    _isInitialized = true;
    notifyListeners();
  }

  Future<void> toggleDarkMode() async {
    _isDarkMode = !_isDarkMode;
    await _storage.write(key: 'dark_mode', value: _isDarkMode.toString());
    notifyListeners();
  }

  Future<void> setDarkMode(bool value) async {
    _isDarkMode = value;
    await _storage.write(key: 'dark_mode', value: value.toString());
    notifyListeners();
  }

  Future<void> setAuth(String token, Map<String, dynamic> user) async {
    _token = token;
    _user = user;
    await _storage.write(key: 'token', value: token);
    await _storage.write(key: 'user', value: json.encode(user));
    notifyListeners();
  }

  Future<void> logout() async {
    _token = null;
    _user = null;
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'user');
    notifyListeners();
  }
}
