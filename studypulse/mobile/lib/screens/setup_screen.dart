import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../api/api_service.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final _api = ApiService();
  List _exams = [];
  bool _loading = true;
  int? _selectedId;

  @override
  void initState() {
    super.initState();
    _fetchExams();
  }

  Future<void> _fetchExams() async {
    try {
      final response = await _api.getExams();
      setState(() {
        _exams = response.data;
        _loading = false;
      });
    } catch (e) {
      if (mounted) Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Select Your Exam'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Skip')),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF43B02A)))
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: 'Search exams...',
                      prefixIcon: const Icon(LucideIcons.search, size: 20),
                      filled: true,
                      fillColor: const Color(0xFFF7F7F7),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                    ),
                  ),
                ),
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1,
                    ),
                    itemCount: _exams.length,
                    itemBuilder: (context, index) {
                      final exam = _exams[index];
                      final isSelected = _selectedId == exam['id'];
                      return GestureDetector(
                        onTap: () => setState(() => _selectedId = exam['id']),
                        child: Container(
                          decoration: BoxDecoration(
                            border: Border.all(color: isSelected ? const Color(0xFF43B02A) : const Color(0xFFE8E8E8), width: 2),
                            borderRadius: BorderRadius.circular(12),
                            color: isSelected ? const Color(0xFFE8F5E3) : Colors.white,
                          ),
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Text('🎓', style: TextStyle(fontSize: 32)),
                              const SizedBox(height: 12),
                              Text(
                                exam['name'],
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                textAlign: TextAlign.center,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${exam['subject_count']} Subjects',
                                style: const TextStyle(fontSize: 10, color: Color(0xFF43B02A), fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: ElevatedButton(
                      onPressed: _selectedId == null ? null : () async {
                        await _api.updateProfile({'target_exam_id': _selectedId});
                        if (context.mounted) {
                          Navigator.of(context).pop();
                        }
                      },
                      child: const Text('Continue'),
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
