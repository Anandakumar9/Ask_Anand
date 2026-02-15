import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mobile/providers/app_provider.dart';
import 'package:mobile/models/exam.dart';
import 'package:mobile/screens/study_timer_screen.dart';

class StudyTab extends StatefulWidget {
  const StudyTab({super.key});

  @override
  State<StudyTab> createState() => _StudyTabState();
}

class _StudyTabState extends State<StudyTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().loadExams();
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppProvider>();

    if (app.examsLoading && app.exams.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Select Exam',
            style: GoogleFonts.poppins(
                fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text('Choose your exam to start studying',
            style: TextStyle(color: Colors.grey[600])),
        const SizedBox(height: 16),
        if (app.exams.isEmpty)
          Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                children: [
                  Icon(Icons.school_outlined,
                      size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 12),
                  Text('No exams available',
                      style: TextStyle(color: Colors.grey[600], fontSize: 16)),
                ],
              ),
            ),
          )
        else
          ...app.exams.map((exam) => _ExamCard(exam: exam)),
      ],
    );
  }
}

class _ExamCard extends StatelessWidget {
  final Exam exam;
  const _ExamCard({required this.exam});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => _SubjectListScreen(exam: exam),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Icon(Icons.school, color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(exam.name,
                        style: GoogleFonts.poppins(
                            fontSize: 16, fontWeight: FontWeight.w600)),
                    if (exam.description != null)
                      Text(exam.description!,
                          style: TextStyle(
                              color: Colors.grey[600], fontSize: 13)),
                    if (exam.subjects.isNotEmpty)
                      Text('${exam.subjects.length} subjects',
                          style: TextStyle(
                              color: theme.colorScheme.primary, fontSize: 12)),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

// Subject selection screen
class _SubjectListScreen extends StatefulWidget {
  final Exam exam;
  const _SubjectListScreen({required this.exam});

  @override
  State<_SubjectListScreen> createState() => _SubjectListScreenState();
}

class _SubjectListScreenState extends State<_SubjectListScreen> {
  Exam? _examDetail;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadExam();
  }

  Future<void> _loadExam() async {
    final detail =
        await context.read<AppProvider>().loadExamDetail(widget.exam.id);
    if (mounted) {
      setState(() {
        _examDetail = detail ?? widget.exam;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final exam = _examDetail ?? widget.exam;
    return Scaffold(
      appBar: AppBar(title: Text(exam.name)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Select Subject',
                    style: GoogleFonts.poppins(
                        fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                if (exam.subjects.isEmpty)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text('No subjects available',
                          style: TextStyle(color: Colors.grey[600])),
                    ),
                  )
                else
                  ...exam.subjects.map((subject) => Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor:
                                Theme.of(context).colorScheme.secondaryContainer,
                            child: Icon(Icons.subject,
                                color: Theme.of(context)
                                    .colorScheme
                                    .secondary),
                          ),
                          title: Text(subject.name,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w500)),
                          subtitle: subject.description != null
                              ? Text(subject.description!)
                              : null,
                          trailing:
                              const Icon(Icons.arrow_forward_ios, size: 16),
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => _TopicListScreen(
                                  examId: exam.id,
                                  subject: subject,
                                ),
                              ),
                            );
                          },
                        ),
                      )),
              ],
            ),
    );
  }
}

// Topic selection screen
class _TopicListScreen extends StatefulWidget {
  final int examId;
  final Subject subject;
  const _TopicListScreen({required this.examId, required this.subject});

  @override
  State<_TopicListScreen> createState() => _TopicListScreenState();
}

class _TopicListScreenState extends State<_TopicListScreen> {
  List<Topic> _topics = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadTopics();
  }

  Future<void> _loadTopics() async {
    final topics = await context
        .read<AppProvider>()
        .loadTopics(widget.examId, widget.subject.id);
    if (mounted) {
      setState(() {
        _topics = topics;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(widget.subject.name)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Select Topic',
                    style: GoogleFonts.poppins(
                        fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                if (_topics.isEmpty)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text('No topics available',
                          style: TextStyle(color: Colors.grey[600])),
                    ),
                  )
                else
                  ..._topics.map((topic) => Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor:
                                theme.colorScheme.tertiaryContainer,
                            child: Icon(Icons.topic,
                                color: theme.colorScheme.tertiary),
                          ),
                          title: Text(topic.name,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w500)),
                          subtitle: topic.questionCount != null
                              ? Text('${topic.questionCount} questions')
                              : null,
                          trailing:
                              const Icon(Icons.arrow_forward_ios, size: 16),
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => StudyTimerScreen(
                                  topicId: topic.id,
                                  topicName: topic.name,
                                ),
                              ),
                            );
                          },
                        ),
                      )),
              ],
            ),
    );
  }
}
