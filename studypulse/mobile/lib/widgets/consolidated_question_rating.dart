import 'package:flutter/material.dart';
import '../api/api_service.dart';

class ConsolidatedQuestionRating extends StatefulWidget {
  final int testId;
  final List<Map<String, dynamic>> aiQuestions;

  const ConsolidatedQuestionRating({
    Key? key,
    required this.testId,
    required this.aiQuestions,
  }) : super(key: key);

  @override
  State<ConsolidatedQuestionRating> createState() => _ConsolidatedQuestionRatingState();
}

class _ConsolidatedQuestionRatingState extends State<ConsolidatedQuestionRating> {
  final ApiService _apiService = ApiService();
  final TextEditingController _feedbackController = TextEditingController();
  
  int _selectedRating = 0;
  bool _isSubmitting = false;
  bool _hasSubmitted = false;
  String? _errorMessage;
  int _ratedCount = 0;

  @override
  void dispose() {
    _feedbackController.dispose();
    super.dispose();
  }

  Future<void> _submitRating() async {
    if (_selectedRating == 0) {
      setState(() {
        _errorMessage = 'Please select a rating';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      // Rate all AI questions with the same rating
      int successCount = 0;
      int failCount = 0;
      
      for (var question in widget.aiQuestions) {
        try {
          await _apiService.rateQuestion(
            widget.testId,
            question['id'] as int,
            _selectedRating,
            feedback: _feedbackController.text.trim(),
          );
          successCount++;
        } catch (e) {
          debugPrint('Failed to rate question ${question['id']}: $e');
          failCount++;
        }
      }

      setState(() {
        _hasSubmitted = true;
        _isSubmitting = false;
        _ratedCount = successCount;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              failCount > 0
                ? '⚠️ Rated $successCount of ${widget.aiQuestions.length} questions'
                : '✅ Thank you! Rated ${widget.aiQuestions.length} AI questions',
            ),
            backgroundColor: failCount > 0 ? Colors.orange : Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to submit ratings: $e';
        _isSubmitting = false;
      });
    }
  }

  Color _getStarColor(int rating) {
    if (rating <= 4) return Colors.red;
    if (rating <= 6) return Colors.orange;
    if (rating <= 8) return Colors.lightGreen;
    return Colors.green;
  }

  String _getRatingLabel(int rating) {
    if (rating == 0) return 'Tap a star to rate (1-10)';
    if (rating <= 3) return 'Poor Quality';
    if (rating <= 5) return 'Needs Improvement';
    if (rating <= 7) return 'Good';
    if (rating <= 9) return 'Excellent';
    return 'Perfect!';
  }

  @override
  Widget build(BuildContext context) {
    if (widget.aiQuestions.isEmpty) {
      return const SizedBox.shrink();
    }

    if (_hasSubmitted) {
      return Card(
        color: Colors.green.shade50,
        margin: const EdgeInsets.only(bottom: 16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Thank you for rating $_ratedCount AI question${_ratedCount > 1 ? 's' : ''}!',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Colors.green,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                const Icon(Icons.psychology, color: Colors.deepPurple, size: 24),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Rate AI Questions',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.deepPurple.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${widget.aiQuestions.length} questions',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Colors.deepPurple,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Rate all ${widget.aiQuestions.length} AI-generated questions to help us improve quality',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey.shade600,
              ),
            ),
            const SizedBox(height: 16),
            
            // Rating stars (1-10)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(10, (index) {
                final rating = index + 1;
                final isSelected = rating <= _selectedRating;
                
                return GestureDetector(
                  onTap: _isSubmitting ? null : () {
                    setState(() {
                      _selectedRating = rating;
                      _errorMessage = null;
                    });
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Icon(
                      isSelected ? Icons.star : Icons.star_border,
                      color: isSelected ? _getStarColor(_selectedRating) : Colors.grey.shade300,
                      size: 28,
                    ),
                  ),
                );
              }),
            ),
            
            const SizedBox(height: 8),
            
            // Rating label
            Center(
              child: Text(
                _getRatingLabel(_selectedRating),
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: _selectedRating > 0 ? _getStarColor(_selectedRating) : Colors.grey,
                ),
              ),
            ),
            
            if (_selectedRating > 0) ...[
              const SizedBox(height: 16),
              
              // Optional feedback
              TextField(
                controller: _feedbackController,
                decoration: InputDecoration(
                  labelText: 'Optional: Additional feedback',
                  hintText: 'What did you like or dislike about these questions?',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  prefixIcon: const Icon(Icons.comment),
                ),
                maxLines: 2,
                maxLength: 200,
                enabled: !_isSubmitting,
              ),
              
              const SizedBox(height: 12),
              
              // Submit button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSubmitting ? null : _submitRating,
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.send),
                  label: Text(
                    _isSubmitting 
                      ? 'Submitting...' 
                      : 'Submit Rating for All ${widget.aiQuestions.length} Questions'
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            ],
            
            // Error message
            if (_errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                style: const TextStyle(
                  color: Colors.red,
                  fontSize: 12,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
