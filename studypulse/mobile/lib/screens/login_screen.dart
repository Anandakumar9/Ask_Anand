
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api/api_service.dart';
import '../store/app_store.dart';
import '../store/app_theme.dart';
import 'home_screen_exam.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController(text: 'test@studypulse.com');
  final _passwordController = TextEditingController(text: 'password123');
  final _api = ApiService();
  bool _loading = false;
  String? _error;

  Future<void> _handleLogin() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    // Allow login with empty fields, but show a warning if both are empty
    if (email.isEmpty && password.isEmpty) {
      setState(() {
        _error = 'Warning: Logging in with empty credentials.';
      });
    }

    try {
      final response = await _api.login(email, password);
      if (mounted) {
        final store = Provider.of<AppStore>(context, listen: false);
        await store.setAuth(response.data['access_token'], response.data['user']);
        
        // Navigate to home screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeScreenExam()),
        );
      }
    } catch (e) {
      debugPrint('Login Error: $e');
      // Try guest login if regular login fails
      try {
        final guestResponse = await _api.guestLogin();
        if (mounted) {
          final store = Provider.of<AppStore>(context, listen: false);
          await store.setAuth(
            guestResponse.data['access_token'], 
            guestResponse.data['user']
          );
          
          // Navigate to home screen as guest
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const HomeScreenExam()),
          );
        }
        setState(() {
          _error = 'Logged in as guest. Some features may be limited.';
        });
      } catch (guestError) {
        debugPrint('Guest login also failed: $guestError');
        setState(() {
          _error = 'Unable to connect to server. Please check your connection.';
          _loading = false;
        });
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final appStore = Provider.of<AppStore>(context);
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'ExamGenius',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF6366F1),
                      fontStyle: FontStyle.italic,
                      letterSpacing: -2,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Welcome back! Login credentials are optional.',
                    style: TextStyle(
                      color: Color(0xFF767676),
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 48),
                  _buildLabel('Email'),
                  _buildTextField(_emailController, 'Enter your email', false),
                  const SizedBox(height: 20),
                  _buildLabel('Password'),
                  _buildTextField(_passwordController, 'Enter your password', true),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                    ),
                  ],
                  const SizedBox(height: 40),
                  ElevatedButton(
                    onPressed: _loading ? null : _handleLogin,
                    child: _loading
                        ? const SizedBox(
                            height: 24,
                            width: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3),
                          )
                        : const Text('Login'),
                  ),
                  const SizedBox(height: 24),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('Don\'t have an account? '),
                      GestureDetector(
                        onTap: () {},
                        child: const Text(
                          'Register',
                          style: TextStyle(color: Color(0xFF6366F1), fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            Positioned(
              top: 16,
              right: 16,
              child: DarkModeToggle(
                isDarkMode: appStore.isDarkMode,
                onToggle: () => appStore.toggleDarkMode(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        text,
        style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF343538)),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String hint, bool isPassword) {
    return TextField(
      controller: controller,
      obscureText: isPassword,
      decoration: InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFE8E8E8)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF6366F1), width: 2),
        ),
      ),
    );
  }
}
