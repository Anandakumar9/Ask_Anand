import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api/api_service.dart';
import '../store/app_store.dart';
import '../store/app_theme.dart';
import 'study_timer_screen.dart';

class StudyScreen extends StatefulWidget {
  const StudyScreen({super.key});

  @override
  State<StudyScreen> createState() => _StudyScreenState();
}

class _StudyScreenState extends State<StudyScreen> {
  final _api = ApiService();
  List _exams = [];
  int? _selectedExamId;
  String? _selectedExamName;
  List _subjects = [];
  int? _selectedSubjectId;
  String? _selectedSubjectName;
  List _topics = [];
  int? _selectedTopicId;
  String? _selectedTopicName;
  int _selectedDuration = 30;
  bool _loading = true;
  bool _loadingSubjects = false;
  bool _loadingTopics = false;
  bool _isRandomMode = false;

  final List<int> _durationOptions = [5, 10, 15, 20, 30, 45, 60, 90, 120];

  @override
  void initState() {
    super.initState();
    _resetSelections();
    _fetchExams();
  }

  void _resetSelections() {
    _selectedExamId = null;
    _selectedExamName = null;
    _selectedSubjectId = null;
    _selectedSubjectName = null;
    _selectedTopicId = null;
    _selectedTopicName = null;
    _selectedDuration = 30;
    _subjects = [];
    _topics = [];
    _isRandomMode = false;
  }

  Future<void> _fetchExams() async {
    setState(() => _loading = true);
    try {
      final response = await _api.getExams();
      setState(() {
        _exams = response.data;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _fetchSubjects(int examId) async {
    setState(() {
      _loadingSubjects = true;
      _subjects = [];
      _selectedSubjectId = null;
      _topics = [];
      _selectedTopicId = null;
      _selectedTopicName = null;
    });
    try {
      final response = await _api.getSubjects(examId);
      setState(() {
        _subjects = response.data;
        _loadingSubjects = false;
      });
    } catch (e) {
      setState(() => _loadingSubjects = false);
    }
  }

  Future<void> _fetchTopics(int examId, int subjectId) async {
    setState(() {
      _loadingTopics = true;
      _topics = [];
      _selectedTopicId = null;
      _selectedTopicName = null;
    });
    try {
      final response = await _api.getTopics(examId, subjectId);
      setState(() {
        _topics = response.data;
        _loadingTopics = false;
      });
    } catch (e) {
      setState(() => _loadingTopics = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = Provider.of<AppStore>(context).user;
    final appStore = Provider.of<AppStore>(context);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Start Study Session'),
        actions: [
          DarkModeToggle(
            isDarkMode: appStore.isDarkMode,
            onToggle: () => appStore.toggleDarkMode(),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF43B02A)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header Card
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF6366F1).withOpacity(0.3),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.menu_book_rounded, color: Colors.white, size: 28),
                            SizedBox(width: 12),
                            Text(
                              'Study Session',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Welcome, ${user?['name']?.split(' ')[0]}! Select exam → subject → topic to begin',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Step 1: Select Exam
                  _buildSectionHeader('📚 Step 1: Select Exam', Icons.school_rounded),
                  const SizedBox(height: 12),
                  _buildExamSelector(),
                  const SizedBox(height: 24),

                  // Step 2: Select Subject
                  if (_selectedExamId != null) ...[
                    _buildSectionHeader('📖 Step 2: Select Subject', Icons.library_books_rounded),
                    const SizedBox(height: 12),
                    _buildSubjectSelector(),
                    const SizedBox(height: 24),
                  ],

                  // Step 3: Select Topic
                  if (_selectedSubjectId != null) ...[
                    _buildSectionHeader('📝 Step 3: Select Topic', Icons.topic_rounded),
                    const SizedBox(height: 12),
                    _buildTopicSelector(),
                    const SizedBox(height: 24),
                  ],

                  // Step 4: Select Duration
                  if (_selectedTopicId != null || _isRandomMode) ...[
                    _buildSectionHeader('⏱️ Step 4: Select Duration', Icons.timer_rounded),
                    const SizedBox(height: 12),
                    _buildDurationSelector(),
                    const SizedBox(height: 32),
                    
                    // Start Button
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 300),
                        child: ElevatedButton(
                          onPressed: _startStudySession,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _isRandomMode 
                                ? const Color(0xFF8B5CF6) 
                                : const Color(0xFF6366F1),
                            foregroundColor: Colors.white,
                            elevation: 8,
                            shadowColor: (_isRandomMode 
                                ? const Color(0xFF8B5CF6) 
                                : const Color(0xFF6366F1)).withOpacity(0.4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              AnimatedSwitcher(
                                duration: const Duration(milliseconds: 300),
                                child: Icon(
                                  _isRandomMode ? Icons.shuffle_rounded : Icons.play_circle_filled_rounded,
                                  key: ValueKey(_isRandomMode),
                                  size: 28,
                                ),
                              ),
                              const SizedBox(width: 12),
                              AnimatedSwitcher(
                                duration: const Duration(milliseconds: 300),
                                child: Text(
                                  _isRandomMode 
                                      ? 'Start Random $_selectedDuration min Session'
                                      : 'Start $_selectedDuration min Study Session',
                                  key: ValueKey(_isRandomMode),
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Info Card
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _isRandomMode ? const Color(0xFFF3E8FF) : const Color(0xFFEFF6FF),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _isRandomMode ? const Color(0xFFDDD6FE) : const Color(0xFF93C5FD)),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline_rounded, color: _isRandomMode ? const Color(0xFF7C3AED) : const Color(0xFF3B82F6)),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Study for $_selectedDuration minutes, then take a mock test to earn stars!',
                              style: const TextStyle(
                                color: Color(0xFF1E3A8A),
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF6366F1), size: 22),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F2937),
          ),
        ),
      ],
    );
  }

  Widget _buildExamSelector() {
    if (_exams.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: const Text('No exams available'),
        ),
      );
    }

    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: _exams.map((exam) {
        final isSelected = _selectedExamId == exam['id'];
        
        // Exam card icons
        IconData examIcon;
        Color examColor;
        switch (exam['name'].toString().toUpperCase()) {
          case 'UPSC CIVIL SERVICES':
          case 'UPSC':
            examIcon = Icons.account_balance_rounded;
            examColor = const Color(0xFF8B5CF6);
            break;
          case 'NEET UG':
          case 'NEET':
            examIcon = Icons.local_hospital_rounded;
            examColor = const Color(0xFFEC4899);
            break;
          case 'JEE MAIN':
          case 'JEE':
            examIcon = Icons.engineering_rounded;
            examColor = const Color(0xFF3B82F6);
            break;
          case 'CAT':
            examIcon = Icons.business_center_rounded;
            examColor = const Color(0xFFF59E0B);
            break;
          default:
            examIcon = Icons.school_rounded;
            examColor = const Color(0xFF6366F1);
        }
        
        return InkWell(
          onTap: () {
            setState(() {
              _selectedExamId = exam['id'];
              _selectedExamName = exam['name'];
            });
            _fetchSubjects(exam['id']);
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            width: (MediaQuery.of(context).size.width - 48) / 2,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isSelected ? examColor.withOpacity(0.1) : Colors.white,
              border: Border.all(
                color: isSelected ? examColor : const Color(0xFFE5E7EB),
                width: isSelected ? 2 : 1,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: isSelected
                  ? [
                      BoxShadow(
                        color: examColor.withOpacity(0.2),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : null,
            ),
            child: Column(
              children: [
                Icon(
                  examIcon,
                  size: 40,
                  color: isSelected ? examColor : const Color(0xFF9CA3AF),
                ),
                const SizedBox(height: 12),
                Text(
                  exam['name'],
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                    color: isSelected ? examColor : const Color(0xFF1F2937),
                  ),
                  textAlign: TextAlign.center,
                ),
                if (exam['category'] != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    exam['category'],
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF9CA3AF),
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildSubjectSelector() {
    if (_loadingSubjects) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: CircularProgressIndicator(color: Color(0xFF6366F1)),
        ),
      );
    }
    if (_subjects.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('No subjects available for this exam'),
        ),
      );
    }

    return Column(
      children: _subjects.map<Widget>((subject) {
        final isSelected = _selectedSubjectId == subject['id'];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          elevation: isSelected ? 4 : 1,
          color: isSelected ? const Color(0xFFEEF2FF) : Colors.white,
          child: ListTile(
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isSelected
                    ? const Color(0xFF6366F1)
                    : const Color(0xFFE5E7EB),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.library_books_rounded,
                color: isSelected ? Colors.white : const Color(0xFF6B7280),
                size: 24,
              ),
            ),
            title: Text(
              subject['name'],
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                color: isSelected ? const Color(0xFF6366F1) : const Color(0xFF1F2937),
              ),
            ),
            subtitle: subject['description'] != null
                ? Text(
                    subject['description'],
                    style: const TextStyle(fontSize: 12),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  )
                : null,
            trailing: isSelected
                ? const Icon(Icons.check_circle_rounded, color: Color(0xFF6366F1))
                : const Icon(Icons.chevron_right_rounded, color: Color(0xFF9CA3AF)),
            onTap: () {
              setState(() {
                _selectedSubjectId = subject['id'];
                _selectedSubjectName = subject['name'];
              });
              _fetchTopics(_selectedExamId!, subject['id']);
            },
          ),
        );
      }).toList(),
    );
  }

  Widget _buildTopicSelector() {
    if (_loadingTopics) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: CircularProgressIndicator(color: Color(0xFF6366F1)),
        ),
      );
    }
    if (_topics.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('No topics available for this subject'),
        ),
      );
    }

    final bool showRandomButton = _topics.length > 10;

    return Column(
      children: [
        if (showRandomButton) ...[
          GestureDetector(
            onTap: () {
              setState(() {
                _isRandomMode = !_isRandomMode;
                if (_isRandomMode) {
                  _selectedTopicId = null;
                  _selectedTopicName = null;
                }
              });
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                gradient: _isRandomMode 
                    ? const LinearGradient(colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)])
                    : null,
                color: _isRandomMode ? null : Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: _isRandomMode ? Colors.transparent : const Color(0xFF6366F1),
                  width: 2,
                ),
                boxShadow: _isRandomMode ? [
                  BoxShadow(
                    color: const Color(0xFF6366F1).withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ] : null,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    child: Icon(
                      _isRandomMode ? Icons.shuffle_on_rounded : Icons.shuffle_rounded,
                      key: ValueKey(_isRandomMode),
                      color: _isRandomMode ? Colors.white : const Color(0xFF6366F1),
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  AnimatedDefaultTextStyle(
                    duration: const Duration(milliseconds: 300),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: _isRandomMode ? Colors.white : const Color(0xFF6366F1),
                    ),
                    child: Text(_isRandomMode ? 'Random Mode ON' : 'Random Questions'),
                  ),
                  if (_isRandomMode) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'MIX',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (_isRandomMode)
            Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF3C7),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFFCD34D)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: Color(0xFF92400E), size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Questions will be randomly selected from all ${_topics.length} topics',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF92400E),
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
        ..._topics.map<Widget>((topic) {
          final isSelected = _selectedTopicId == topic['id'];
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            elevation: isSelected ? 4 : 1,
            color: isSelected ? const Color(0xFFEEF2FF) : Theme.of(context).cardColor,
            child: ListTile(
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isSelected
                      ? const Color(0xFF6366F1)
                      : const Color(0xFFE5E7EB),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.topic_rounded,
                  color: isSelected ? Colors.white : const Color(0xFF6B7280),
                  size: 24,
                ),
              ),
              title: Text(
                topic['name'],
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                  color: isSelected ? const Color(0xFF6366F1) : Theme.of(context).textTheme.bodyLarge?.color,
                ),
              ),
              trailing: isSelected
                  ? const Icon(Icons.check_circle_rounded, color: Color(0xFF6366F1))
                  : const Icon(Icons.chevron_right_rounded, color: Color(0xFF9CA3AF)),
              onTap: () {
                setState(() {
                  _selectedTopicId = topic['id'];
                  _selectedTopicName = topic['name'];
                  _isRandomMode = false;
                });
              },
            ),
          );
        }).toList(),
      ],
    );
  }

  Widget _buildDurationSelector() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _durationOptions.map((duration) {
        final isSelected = _selectedDuration == duration;
        return ChoiceChip(
          label: Text('$duration min'),
          selected: isSelected,
          onSelected: (selected) {
            setState(() => _selectedDuration = duration);
          },
          selectedColor: const Color(0xFF6366F1),
          labelStyle: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFF6B7280),
            fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
          ),
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: BorderSide(
              color: isSelected ? const Color(0xFF6366F1) : const Color(0xFFE5E7EB),
            ),
          ),
        );
      }).toList(),
    );
  }

  void _startStudySession() {
    // Allow starting if either a topic is selected OR random mode is enabled
    if (_selectedTopicId != null || _isRandomMode) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => StudyTimerScreen(
            topicId: _selectedTopicId ?? -1, // -1 indicates random mode
            topicName: _isRandomMode ? 'Random Mix' : _selectedTopicName!,
            durationMins: _selectedDuration,
            isRandomMode: _isRandomMode,
          ),
        ),
      );
    }
  }
}
