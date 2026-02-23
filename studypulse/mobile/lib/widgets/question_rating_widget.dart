import 'package:flutter/material.dart';
import '../api/api_service.dart';

class QuestionRatingWidget extends StatefulWidget {
  final int testId;
  final int questionId;
  final String questionText;
  final bool isAIGenerated;

  const QuestionRatingWidget({
    Key? key,
    required this.testId,
    required this.questionId,
    required this.questionText,
    required this.isAIGenerated,
  }) : super(key: key);

  @override
  State<QuestionRatingWidget> createState() => _QuestionRatingWidgetState();
}

class _QuestionRatingWidgetState extends State<QuestionRatingWidget> {
  final ApiService _apiService = ApiService();
  final TextEditingController _feedbackController = TextEditingController();
  
  int _selectedRating = 0;
  bool _isSubmitting = false;
  bool _hasSubmitted = false;
  String? _errorMessage;

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
      final response = await _apiService.rateQuestion(
        widget.testId,
        widget.questionId,
        _selectedRating,
        feedback: _feedbackController.text.trim(),
      );

      setState(() {
        _hasSubmitted = true;
        _isSubmitting = false;
      });

      // Show success message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.data['message'] ?? '✅ Thank you for your feedback!'),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to submit rating: $e';
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
    if (!widget.isAIGenerated) {
      return const SizedBox.shrink(); // Don't show for non-AI questions
    }

    if (_hasSubmitted) {
      return Card(
        color: Colors.green.shade50,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 32),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Thank you for rating this question!',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Colors.green,
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
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Icon(Icons.psychology, color: Colors.deepPurple, size: 24),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Rate this AI question',
                    style: TextStyle(
                      fontSize: 16,
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
                  child: Row(
                    children: [
                      Icon(Icons.auto_awesome, size: 12, color: Colors.deepPurple),
                      const SizedBox(width: 4),
                      Text(
                        'AI Generated',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Colors.deepPurple,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Display the actual question text
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Text(
                widget.questionText,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  height: 1.4,
                ),
              ),
            ),
            
            const SizedBox(height: 8),
            Text(
              'Help us improve question quality',
              style: TextStyle(
                fontSize: 12,
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
                  labelText: 'Optional: Tell us more',
                  hintText: 'What did you like or dislike?',
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
                  label: Text(_isSubmitting ? 'Submitting...' : 'Submit Rating'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
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
