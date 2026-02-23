import 'package:flutter/material.dart';
import 'package:mobile/screens/home_screen_exam.dart';
import 'package:mobile/screens/login_screen.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mobile/api/api_service.dart';
import 'package:provider/provider.dart';
import '../store/app_store.dart';
import '../store/app_theme.dart';

class WelcomeScreenExam extends StatefulWidget {
  const WelcomeScreenExam({Key? key}) : super(key: key);

  @override
  State<WelcomeScreenExam> createState() => _WelcomeScreenExamState();
}

class _WelcomeScreenExamState extends State<WelcomeScreenExam> {
  final _storage = const FlutterSecureStorage();
  final _api = ApiService();
  bool _isLoading = true;
  bool _isLoggingIn = false;

  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    // Check if user is already logged in
    final token = await _storage.read(key: 'token');
    
    if (token != null) {
      // Returning user - show loading screen briefly then navigate
      await Future.delayed(const Duration(seconds: 2));
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const HomeScreenExam()),
        );
      }
    } else {
      // First time user - show welcome screen
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _handleGuestLogin() async {
    setState(() => _isLoggingIn = true);
    
    try {
      // Perform guest login
      final response = await _api.guestLogin();
      
      // Store token
      await _storage.write(key: 'token', value: response.data['access_token']);
      await _storage.write(key: 'userId', value: response.data['user']['id'].toString());
      await _storage.write(key: 'userName', value: response.data['user']['name']);
      
      // Navigate to home
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const HomeScreenExam()),
        );
      }
    } catch (e) {
      debugPrint('Guest login error: $e');
      // Show error message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to connect. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoggingIn = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      // Loading screen for returning users
      return Scaffold(
        body: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF6366F1), // Purple
                Color(0xFF8B5CF6),
              ],
            ),
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // App Logo
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Icon(
                    Icons.school,
                    size: 60,
                    color: Color(0xFF6366F1),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'ExamGenius',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Master UPSC with AI precision.',
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.white70,
                  ),
                ),
                const SizedBox(height: 40),
                const CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Welcome screen for first-time users
    return Consumer<AppStore>(
      builder: (context, appStore, child) {
        return Scaffold(
          body: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.white,
                  Color(0xFFF3F4F6),
                ],
              ),
            ),
            child: SafeArea(
              child: Stack(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Spacer(),
                        
                        // App Logo
                        Container(
                          width: 100,
                          height: 100,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                            ),
                            borderRadius: BorderRadius.circular(24),
                          ),
                          child: const Icon(
                            Icons.school,
                            size: 60,
                            color: Colors.white,
                          ),
                        ),
                        
                        const SizedBox(height: 24),
                        
                        // App Name
                        const Text(
                          'ExamGenius',
                          style: TextStyle(
                            fontSize: 36,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF6366F1),
                          ),
                        ),
                        
                        const SizedBox(height: 8),
                        
                        // Tagline
                        const Text(
                          'Master UPSC with AI precision.',
                          style: TextStyle(
                            fontSize: 16,
                            color: Color(0xFF6B7280),
                          ),
                        ),
                        
                        const SizedBox(height: 60),
                        
                        // Features
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _buildFeatureIcon(Icons.psychology, 'AI PATTERNS'),
                            _buildFeatureIcon(Icons.emoji_events, 'GAMIFIED'),
                            _buildFeatureIcon(Icons.assignment, 'MOCK TESTS'),
                          ],
                        ),
                        
                        const Spacer(),
                        
                        // Get Started Button
                        SizedBox(
                          width: double.infinity,
                          height: 56,
                          child: ElevatedButton(
                            onPressed: _isLoggingIn ? null : _handleGuestLogin,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF6366F1),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                              elevation: 0,
                            ),
                            child: _isLoggingIn
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: const [
                                      Text(
                                        'Get Started',
                                        style: TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                      SizedBox(width: 8),
                                      Icon(Icons.arrow_forward, size: 20),
                                    ],
                                  ),
                          ),
                        ),
                        
                        const SizedBox(height: 16),
                        
                        // Sign In Link
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text(
                              'Already a scholar? ',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 14,
                              ),
                            ),
                            TextButton(
                              onPressed: () {
                                Navigator.of(context).pushReplacement(
                                  MaterialPageRoute(
                                    builder: (context) => const LoginScreen(),
                                  ),
                                );
                              },
                              child: const Text(
                                'Sign In',
                                style: TextStyle(
                                  color: Color(0xFF6366F1),
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 8),
                        
                        // Footer
                        const Text(
                          '© 2026 EXAMGENIUS APP',
                          style: TextStyle(
                            color: Color(0xFF9CA3AF),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Positioned(
                    top: 0,
                    right: 0,
                    child: DarkModeToggle(
                      isDarkMode: appStore.isDarkMode,
                      onToggle: () => appStore.toggleDarkMode(),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildFeatureIcon(IconData icon, String label) {
    return Column(
      children: [
        Container(
          width: 70,
          height: 70,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Color(0xFF6366F1).withOpacity(0.3),
                blurRadius: 12,
                offset: Offset(0, 4),
              ),
            ],
          ),
          child: Icon(
            icon,
            size: 36,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.bold,
            color: Color(0xFF6366F1),
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }
}
