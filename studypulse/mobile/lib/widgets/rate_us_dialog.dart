import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';

class RateUsDialog extends StatelessWidget {
  const RateUsDialog({Key? key}) : super(key: key);

  // Store URLs - will be updated when publishing
  static const String playStoreUrl = 'https://play.google.com/store/apps/details?id=com.studypulse.app';
  static const String appStoreUrl = 'https://apps.apple.com/app/studypulse/id1234567890';

  /// Show rate us dialog if user has completed at least 3 tests
  /// and hasn't rated yet or dismissed recently
  static Future<void> showIfEligible(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    
    // Check if user has rated or dismissed
    final hasRated = prefs.getBool('has_rated_app') ?? false;
    final lastDismissed = prefs.getInt('rate_us_last_dismissed') ?? 0;
    final testsCompleted = prefs.getInt('tests_completed') ?? 0;
    
    // Don't show if:
    // 1. User already rated
    // 2. User dismissed within last 7 days
    // 3. User has completed less than 3 tests
    final now = DateTime.now().millisecondsSinceEpoch;
    final sevenDaysAgo = now - (7 * 24 * 60 * 60 * 1000);
    
    if (hasRated) {
      return; // Already rated, never show again
    }
    
    if (lastDismissed > sevenDaysAgo) {
      return; // Dismissed recently, wait 7 days
    }
    
    if (testsCompleted < 3) {
      return; // Need at least 3 completed tests
    }
    
    // User is eligible - show dialog
    if (context.mounted) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const RateUsDialog(),
      );
    }
  }

  /// Increment tests completed counter
  static Future<void> incrementTestsCompleted() async {
    final prefs = await SharedPreferences.getInstance();
    final current = prefs.getInt('tests_completed') ?? 0;
    await prefs.setInt('tests_completed', current + 1);
  }

  Future<void> _rateOnPlayStore() async {
    final Uri url = Uri.parse(playStoreUrl);
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
      
      // Mark as rated
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('has_rated_app', true);
    }
  }

  Future<void> _rateOnAppStore() async {
    final Uri url = Uri.parse(appStoreUrl);
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
      
      // Mark as rated
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('has_rated_app', true);
    }
  }

  Future<void> _dismissDialog(BuildContext context) async {
    // Record dismissal time
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(
      'rate_us_last_dismissed',
      DateTime.now().millisecondsSinceEpoch,
    );
    
    if (context.mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      title: Row(
        children: [
          const Icon(Icons.star, color: Colors.amber, size: 32),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Enjoying StudyPulse?',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Your feedback helps us improve and reach more students!',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 16),
          const Text(
            'Rate us on your platform:',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          
          // Star rating visualization
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              5,
              (index) => const Icon(
                Icons.star,
                color: Colors.amber,
                size: 36,
              ),
            ),
          ),
        ],
      ),
      actions: [
        // Maybe Later button
        TextButton(
          onPressed: () => _dismissDialog(context),
          child: const Text(
            'Maybe Later',
            style: TextStyle(color: Colors.grey),
          ),
        ),
        
        // Play Store button
        ElevatedButton.icon(
          onPressed: () {
            _rateOnPlayStore();
            Navigator.of(context).pop();
          },
          icon: const Icon(Icons.android, size: 20),
          label: const Text('Play Store'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.green,
            foregroundColor: Colors.white,
          ),
        ),
        
        // App Store button
        ElevatedButton.icon(
          onPressed: () {
            _rateOnAppStore();
            Navigator.of(context).pop();
          },
          icon: const Icon(Icons.apple, size: 20),
          label: const Text('App Store'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black87,
            foregroundColor: Colors.white,
          ),
        ),
      ],
      actionsPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    );
  }
}
