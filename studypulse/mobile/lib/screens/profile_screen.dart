import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';
import '../store/app_store.dart';
import '../api/api_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _api = ApiService();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  String? _targetExam;
  bool _loading = false;
  bool _editMode = false;
  Map<String, dynamic> _stats = {};

  @override
  void initState() {
    super.initState();
    _loadUserData();
    _fetchStats();
  }

  Future<void> _fetchStats() async {
    try {
      final response = await _api.getDashboard();
      if (mounted) {
        setState(() {
          _stats = (response.data['stats'] as Map<String, dynamic>?) ?? {};
        });
      }
    } catch (_) {
      // Use empty stats on failure
    }
  }

  void _loadUserData() {
    final user = Provider.of<AppStore>(context, listen: false).user;
    if (user != null) {
      _nameController.text = user['name'] ?? '';
      _emailController.text = user['email'] ?? '';
      _phoneController.text = user['phone'] ?? '';
      _targetExam = user['target_exam_name'];
    }
  }

  Future<void> _updateProfile() async {
    setState(() => _loading = true);
    try {
      await _api.updateProfile({
        'name': _nameController.text,
        'phone': _phoneController.text,
      });
      
      if (mounted) {
        setState(() => _editMode = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile updated successfully'),
            backgroundColor: Color(0xFF43B02A),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to update profile'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = Provider.of<AppStore>(context).user;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F7),
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          if (!_editMode)
            IconButton(
              icon: const Icon(LucideIcons.edit2),
              onPressed: () => setState(() => _editMode = true),
            ),
          IconButton(
            icon: const Icon(LucideIcons.settings),
            onPressed: () {},
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Profile Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 50,
                    backgroundColor: const Color(0xFFE8F5E3),
                    child: Text(
                      user?['name']?[0] ?? 'U',
                      style: const TextStyle(
                        fontSize: 40,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF43B02A),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    user?['name'] ?? 'User',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?['email'] ?? '',
                    style: const TextStyle(
                      color: Color(0xFF767676),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E3),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          LucideIcons.target,
                          size: 14,
                          color: Color(0xFF43B02A),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _targetExam ?? 'No exam selected',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF43B02A),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Personal Information
          const Text(
            'Personal Information',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildInfoRow(
                    LucideIcons.user,
                    'Full Name',
                    _nameController,
                    _editMode,
                  ),
                  const Divider(height: 24),
                  _buildInfoRow(
                    LucideIcons.mail,
                    'Email',
                    _emailController,
                    false, // Email cannot be edited
                  ),
                  const Divider(height: 24),
                  _buildInfoRow(
                    LucideIcons.phone,
                    'Phone',
                    _phoneController,
                    _editMode,
                  ),
                ],
              ),
            ),
          ),

          if (_editMode) ...[
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      setState(() => _editMode = false);
                      _loadUserData(); // Reset to original values
                    },
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _loading ? null : _updateProfile,
                    child: _loading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Save Changes'),
                  ),
                ),
              ],
            ),
          ],

          const SizedBox(height: 24),

          // Statistics
          const Text(
            'Statistics',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildStatCard('⭐', '${_stats['total_stars'] ?? 0}', 'Total Stars'),
              const SizedBox(width: 8),
              _buildStatCard('🔥', '${_stats['study_streak'] ?? 0} Days', 'Streak'),
              const SizedBox(width: 8),
              _buildStatCard('📚', '${_stats['tests_completed'] ?? 0}', 'Tests Taken'),
            ],
          ),

          const SizedBox(height: 24),

          // Settings
          const Text(
            'Settings',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(LucideIcons.target, color: Color(0xFF43B02A)),
                  title: const Text('Change Target Exam'),
                  trailing: const Icon(LucideIcons.chevronRight, size: 16),
                  onTap: () {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(LucideIcons.bell, color: Color(0xFF43B02A)),
                  title: const Text('Notifications'),
                  trailing: const Icon(LucideIcons.chevronRight, size: 16),
                  onTap: () {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(LucideIcons.helpCircle, color: Color(0xFF43B02A)),
                  title: const Text('Help & Support'),
                  trailing: const Icon(LucideIcons.chevronRight, size: 16),
                  onTap: () {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(LucideIcons.logOut, color: Colors.red),
                  title: const Text('Logout'),
                  onTap: () {
                    Provider.of<AppStore>(context, listen: false).logout();
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(
    IconData icon,
    String label,
    TextEditingController controller,
    bool editable,
  ) {
    return Row(
      children: [
        Icon(icon, size: 20, color: const Color(0xFF43B02A)),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF767676),
                ),
              ),
              const SizedBox(height: 4),
              editable
                  ? TextField(
                      controller: controller,
                      decoration: const InputDecoration(
                        isDense: true,
                        contentPadding: EdgeInsets.zero,
                        border: InputBorder.none,
                      ),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    )
                  : Text(
                      controller.text.isEmpty ? 'Not set' : controller.text,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(String emoji, String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE8E8E8)),
        ),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 24)),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            Text(
              label,
              style: const TextStyle(
                fontSize: 10,
                color: Color(0xFF767676),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }
}
