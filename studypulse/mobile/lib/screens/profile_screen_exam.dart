import 'package:flutter/material.dart';
import 'package:mobile/api/api_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mobile/screens/login_screen.dart';

class ProfileScreenExam extends StatefulWidget {
  const ProfileScreenExam({Key? key}) : super(key: key);

  @override
  State<ProfileScreenExam> createState() => _ProfileScreenExamState();
}

class _ProfileScreenExamState extends State<ProfileScreenExam> {
  final _api = ApiService();
  final _storage = const FlutterSecureStorage();
  Map<String, dynamic>? _profileData;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _loading = true);
    try {
      final response = await _api.get('/profile/stats');
      setState(() {
        _profileData = response.data;
        _loading = false;
      });
    } catch (e) {
      debugPrint('Error loading profile: $e');
      setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    await _storage.deleteAll();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        title: const Text(
          'Profile',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1F2937),
        elevation: 0,
        actions: [
          IconButton(
            onPressed: _showEditDialog,
            icon: const Icon(Icons.edit_outlined),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            color: const Color(0xFFE5E7EB),
            height: 1,
          ),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadProfile,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                child: Column(
                  children: [
                    _buildProfileHeader(),
                    _buildStatsSection(),
                    _buildStreakSection(),
                    _buildProficiencySection(),
                    _buildGoalsSection(),
                    _buildSettingsSection(),
                    const SizedBox(height: 80),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildProfileHeader() {
    final basicInfo = _profileData?['basic_info'] ?? {};
    final username = basicInfo['username'] ?? 'User';
    final email = basicInfo['email'] ?? '';
    final displayName = basicInfo['display_name'] ?? username;
    
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Stack(
            children: [
              CircleAvatar(
                radius: 50,
                backgroundColor: const Color(0xFF6366F1),
                child: Text(
                  displayName[0].toUpperCase(),
                  style: const TextStyle(
                    fontSize: 40,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: const BoxDecoration(
                    color: Color(0xFF6366F1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.camera_alt, size: 16, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            displayName,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1F2937),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            email,
            style: const TextStyle(
              fontSize: 14,
              color: Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsSection() {
    final stats = _profileData?['activity_stats'] ?? {};
    final totalSessions = stats['total_sessions'] ?? 0;
    final totalTests = stats['total_tests'] ?? 0;
    final totalStars = stats['total_stars'] ?? 0;
    final avgScore = (stats['average_score'] ?? 0.0).toStringAsFixed(1);
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.bar_chart, color: Color(0xFF6366F1), size: 20),
              SizedBox(width: 8),
              Text(
                'Overall Statistics',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  Icons.schedule_rounded,
                  totalSessions.toString(),
                  'Sessions',
                  const Color(0xFF3B82F6),
                ),
              ),
              Expanded(
                child: _buildStatItem(
                  Icons.assignment_outlined,
                  totalTests.toString(),
                  'Tests',
                  const Color(0xFF8B5CF6),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  Icons.star_rounded,
                  totalStars.toString(),
                  'Stars',
                  const Color(0xFFFBBF24),
                ),
              ),
              Expanded(
                child: _buildStatItem(
                  Icons.trending_up,
                  '$avgScore%',
                  'Avg Score',
                  const Color(0xFF10B981),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(IconData icon, String value, String label, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStreakSection() {
    final streak = _profileData?['study_streak'] ?? 0;
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFF7ED), Color(0xFFFFEDD5)],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF97316)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: const [
              Icon(Icons.local_fire_department, color: Color(0xFFF97316), size: 28),
              SizedBox(width: 8),
              Text(
                'Study Streak',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '$streak',
            style: const TextStyle(
              fontSize: 48,
              fontWeight: FontWeight.bold,
              color: Color(0xFFF97316),
            ),
          ),
          Text(
            streak == 1 ? 'day' : 'days',
            style: const TextStyle(
              fontSize: 16,
              color: Color(0xFF6B7280),
            ),
          ),
          const SizedBox(height: 16),
          _buildStreakDays(streak),
        ],
      ),
    );
  }

  Widget _buildStreakDays(int streak) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(7, (index) {
        final isActive = index < (streak % 7 == 0 && streak > 0 ? 7 : streak % 7);
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: isActive ? const Color(0xFFF97316) : const Color(0xFFE5E7EB),
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              '${index + 1}',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: isActive ? Colors.white : const Color(0xFF9CA3AF),
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildProficiencySection() {
    final proficiency = _profileData?['subject_proficiency'] ?? {};
    
    if (proficiency.isEmpty) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.insights, color: Color(0xFF6366F1), size: 20),
              SizedBox(width: 8),
              Text(
                'Subject Proficiency',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          ...proficiency.entries.map((entry) {
            final subjectName = entry.key;
            final data = entry.value as Map<String, dynamic>;
            final avgScore = (data['average_score'] ?? 0.0).toDouble();
            final testCount = data['test_count'] ?? 0;
            
            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: _buildProficiencyBar(subjectName, avgScore, testCount),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildProficiencyBar(String subject, double score, int tests) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                subject,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1F2937),
                ),
              ),
            ),
            Text(
              '${score.toStringAsFixed(1)}%',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Color(0xFF6366F1),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: score / 100,
            minHeight: 8,
            backgroundColor: const Color(0xFFE5E7EB),
            valueColor: AlwaysStoppedAnimation<Color>(
              score >= 85 ? const Color(0xFF10B981) : const Color(0xFF6366F1),
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '$tests tests completed',
          style: const TextStyle(
            fontSize: 11,
            color: Color(0xFF9CA3AF),
          ),
        ),
      ],
    );
  }

  Widget _buildGoalsSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.emoji_events, color: Color(0xFF6366F1), size: 20),
              SizedBox(width: 8),
              Text(
                'Performance Goals',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildGoalItem(
            '🎯 Achieve 100% Accuracy',
            'Target score of 100% in all subjects',
            100.0,
          ),
          const SizedBox(height: 12),
          _buildGoalItem(
            '⭐ Collect 100 Stars',
            'Earn stars by scoring 85% or higher',
            (_profileData?['activity_stats']?['total_stars'] ?? 0) / 100 * 100,
          ),
          const SizedBox(height: 12),
          _buildGoalItem(
            '🔥 30-Day Streak',
            'Study consistently for 30 days',
            (_profileData?['study_streak'] ?? 0) / 30 * 100,
          ),
        ],
      ),
    );
  }

  Widget _buildGoalItem(String title, String description, double progress) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: Color(0xFF1F2937),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: const TextStyle(
              fontSize: 12,
              color: Color(0xFF6B7280),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress.clamp(0, 100) / 100,
                    minHeight: 6,
                    backgroundColor: const Color(0xFFE5E7EB),
                    valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6366F1)),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '${progress.clamp(0, 100).toStringAsFixed(0)}%',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF6366F1),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsSection() {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          _buildSettingItem(Icons.notifications_outlined, 'Notifications', () {}),
          const Divider(height: 1, indent: 56),
          _buildSettingItem(Icons.security_outlined, 'Privacy & Security', () {}),
          const Divider(height: 1, indent: 56),
          _buildSettingItem(Icons.help_outline, 'Help & Support', () {}),
          const Divider(height: 1, indent: 56),
          _buildSettingItem(Icons.info_outline, 'About', () {}),
          const Divider(height: 1, indent: 56),
          _buildSettingItem(Icons.logout, 'Logout', _logout, isDestructive: true),
        ],
      ),
    );
  }

  Widget _buildSettingItem(IconData icon, String title, VoidCallback onTap, {bool isDestructive = false}) {
    return ListTile(
      leading: Icon(
        icon,
        color: isDestructive ? const Color(0xFFEF4444) : const Color(0xFF6B7280),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: isDestructive ? const Color(0xFFEF4444) : const Color(0xFF1F2937),
          fontWeight: FontWeight.w500,
        ),
      ),
      trailing: Icon(
        Icons.arrow_forward_ios,
        size: 16,
        color: isDestructive ? const Color(0xFFEF4444) : const Color(0xFF9CA3AF),
      ),
      onTap: onTap,
    );
  }

  void _showEditDialog() {
    final displayNameController = TextEditingController(
      text: _profileData?['basic_info']?['display_name'] ?? '',
    );
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Profile'),
        content: TextField(
          controller: displayNameController,
          decoration: const InputDecoration(
            labelText: 'Display Name',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              try {
                await _api.put('/profile/update', data: {
                  'display_name': displayNameController.text,
                });
                Navigator.pop(context);
                _loadProfile();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Profile updated successfully')),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Error: $e')),
                );
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}
