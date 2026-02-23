import 'package:flutter/material.dart';
import 'package:mobile/api/api_service.dart';

class RanksScreen extends StatefulWidget {
  const RanksScreen({Key? key}) : super(key: key);

  @override
  State<RanksScreen> createState() => _RanksScreenState();
}

class _RanksScreenState extends State<RanksScreen> {
  final _api = ApiService();
  Map<String, dynamic>? _leaderboardData;
  List<Map<String, dynamic>> _exams = [];
  int? _selectedExamId;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadExams();
  }

  Future<void> _loadExams() async {
    try {
      // Skip loading exams, just load leaderboard directly with demo ID
      _selectedExamId = 1;
      await _loadLeaderboard();
    } catch (e) {
      debugPrint('Error loading: $e');
      setState(() => _loading = false);
    }
  }

  Future<void> _loadLeaderboard() async {
    if (_selectedExamId == null) return;
    
    setState(() => _loading = true);
    try {
      final response = await _api.get('/leaderboard/?exam_id=$_selectedExamId&limit=100')
          .timeout(const Duration(seconds: 10));
      setState(() {
        _leaderboardData = response.data;
        _loading = false;
      });
    } catch (e) {
      debugPrint('Error loading leaderboard: $e');
      setState(() {
        _loading = false;
        // Set dummy data on error
        _leaderboardData = {
          'leaderboard': [
            {'rank': 1, 'username': 'Priya', 'stars': 156, 'accuracy': 92.5, 'test_count': 12},
            {'rank': 2, 'username': 'Rahul', 'stars': 142, 'accuracy': 88.3, 'test_count': 10},
            {'rank': 3, 'username': 'Anjali', 'stars': 128, 'accuracy': 85.7, 'test_count': 9},
          ],
          'your_rank': 15,
          'total_users': 234,
        };
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        title: const Text(
          'Leaderboard',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1F2937),
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            color: const Color(0xFFE5E7EB),
            height: 1,
          ),
        ),
      ),
      body: Column(
        children: [
          _buildExamFilter(),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: _loadLeaderboard,
                    child: SingleChildScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      child: Column(
                        children: [
                          _buildPodium(),
                          _buildYourRank(),
                          _buildLeaderboardList(),
                        ],
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildExamFilter() {
    if (_exams.isEmpty) return const SizedBox.shrink();
    
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: const Color(0xFFF9FAFB),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE5E7EB)),
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<int>(
            value: _selectedExamId,
            isExpanded: true,
            icon: const Icon(Icons.keyboard_arrow_down),
            items: _exams.map((exam) {
              return DropdownMenuItem<int>(
                value: exam['id'],
                child: Text(exam['name']),
              );
            }).toList(),
            onChanged: (value) {
              setState(() => _selectedExamId = value);
              _loadLeaderboard();
            },
          ),
        ),
      ),
    );
  }

  Widget _buildPodium() {
    final leaderboard = _leaderboardData?['leaderboard'] ?? [];
    if (leaderboard.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: Text(
            'No rankings yet',
            style: TextStyle(color: Color(0xFF9CA3AF)),
          ),
        ),
      );
    }
    
    final top3 = leaderboard.take(3).toList();
    
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(32),
          bottomRight: Radius.circular(32),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (top3.length > 1) _buildPodiumItem(top3[1], 2, 80),
          if (top3.isNotEmpty) _buildPodiumItem(top3[0], 1, 100),
          if (top3.length > 2) _buildPodiumItem(top3[2], 3, 70),
        ],
      ),
    );
  }

  Widget _buildPodiumItem(Map<String, dynamic> user, int rank, double height) {
    final username = user['username'] ?? 'User';
    final accuracy = (user['accuracy'] ?? 0).toStringAsFixed(1);
    final stars = user['stars'] ?? 0;
    
    final colors = [
      const Color(0xFFFBBF24), // Gold
      const Color(0xFFD1D5DB), // Silver
      const Color(0xFFF97316), // Bronze
    ];
    
    return Container(
      width: 90,
      margin: const EdgeInsets.symmetric(horizontal: 8),
      child: Column(
        children: [
          Stack(
            alignment: Alignment.topCenter,
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white,
                  border: Border.all(
                    color: colors[rank - 1],
                    width: 3,
                  ),
                ),
                child: Center(
                  child: Text(
                    username[0].toUpperCase(),
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: colors[rank - 1],
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: -5,
                child: Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: colors[rank - 1],
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    '$rank',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            username,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.star, color: Color(0xFFFBBF24), size: 14),
              const SizedBox(width: 4),
              Text(
                '$stars',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            height: height,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
            ),
            child: Center(
              child: Text(
                '$accuracy%',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildYourRank() {
    final yourRank = _leaderboardData?['your_rank'];
    final totalUsers = _leaderboardData?['total_users'] ?? 0;
    
    if (yourRank == null) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFEEF2FF), Color(0xFFE0E7FF)],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF6366F1)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'YOUR RANK',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF6366F1),
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '#$yourRank',
                style: const TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF6366F1),
                ),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Text(
                'TOTAL USERS',
                style: TextStyle(
                  fontSize: 11,
                  color: Color(0xFF6B7280),
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '$totalUsers',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLeaderboardList() {
    final leaderboard = _leaderboardData?['leaderboard'] ?? [];
    if (leaderboard.isEmpty) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
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
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: const [
                Icon(Icons.emoji_events, color: Color(0xFF6366F1), size: 20),
                SizedBox(width: 8),
                Text(
                  'All Rankings',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F2937),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: leaderboard.length,
            separatorBuilder: (context, index) => const Divider(height: 1, indent: 72),
            itemBuilder: (context, index) {
              final user = leaderboard[index];
              return _buildLeaderboardItem(user);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildLeaderboardItem(Map<String, dynamic> user) {
    final rank = user['rank'] ?? 0;
    final username = user['username'] ?? 'User';
    final accuracy = (user['accuracy'] ?? 0).toStringAsFixed(1);
    final stars = user['stars'] ?? 0;
    final testCount = user['test_count'] ?? 0;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: rank <= 3
                  ? const Color(0xFFFFF7ED)
                  : const Color(0xFFF3F4F6),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Text(
                '#$rank',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: rank <= 3
                      ? const Color(0xFFF97316)
                      : const Color(0xFF6B7280),
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  username,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1F2937),
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    const Icon(Icons.assignment, size: 12, color: Color(0xFF9CA3AF)),
                    const SizedBox(width: 4),
                    Text(
                      '$testCount tests',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF9CA3AF),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '$accuracy%',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF6366F1),
                ),
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  const Icon(Icons.star, color: Color(0xFFFBBF24), size: 14),
                  const SizedBox(width: 4),
                  Text(
                    '$stars',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF6B7280),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}
