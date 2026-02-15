class Question {
  final int id;
  final String questionText;
  final List<String> options;
  final String? correctAnswer;
  final String? explanation;
  final String? difficulty;
  final bool isAiGenerated;

  Question({
    required this.id,
    required this.questionText,
    required this.options,
    this.correctAnswer,
    this.explanation,
    this.difficulty,
    this.isAiGenerated = false,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json['id'] as int,
      questionText: json['question_text'] as String? ?? '',
      options: (json['options'] as List<dynamic>?)
              ?.map((o) => o.toString())
              .toList() ??
          [],
      correctAnswer: json['correct_answer'] as String?,
      explanation: json['explanation'] as String?,
      difficulty: json['difficulty'] as String?,
      isAiGenerated: json['is_ai_generated'] as bool? ?? false,
    );
  }
}

class MockTest {
  final int id;
  final int? topicId;
  final int? sessionId;
  final List<Question> questions;
  final int questionCount;

  MockTest({
    required this.id,
    this.topicId,
    this.sessionId,
    this.questions = const [],
    this.questionCount = 0,
  });

  factory MockTest.fromJson(Map<String, dynamic> json) {
    return MockTest(
      id: json['test_id'] as int? ?? json['id'] as int? ?? 0,
      topicId: json['topic_id'] as int?,
      sessionId: json['session_id'] as int?,
      questions: (json['questions'] as List<dynamic>?)
              ?.map((q) => Question.fromJson(q as Map<String, dynamic>))
              .toList() ??
          [],
      questionCount: json['question_count'] as int? ?? 0,
    );
  }
}

class TestResult {
  final int testId;
  final int totalQuestions;
  final int correctAnswers;
  final double score;
  final bool starEarned;
  final int totalTimeSeconds;
  final List<QuestionResult>? questionResults;

  TestResult({
    required this.testId,
    required this.totalQuestions,
    required this.correctAnswers,
    required this.score,
    required this.starEarned,
    this.totalTimeSeconds = 0,
    this.questionResults,
  });

  factory TestResult.fromJson(Map<String, dynamic> json) {
    return TestResult(
      testId: json['test_id'] as int? ?? 0,
      totalQuestions: json['total_questions'] as int? ?? 0,
      correctAnswers: json['correct_answers'] as int? ?? 0,
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      starEarned: json['star_earned'] as bool? ?? false,
      totalTimeSeconds: json['total_time_seconds'] as int? ?? 0,
      questionResults: (json['question_results'] as List<dynamic>?)
          ?.map((q) => QuestionResult.fromJson(q as Map<String, dynamic>))
          .toList(),
    );
  }
}

class QuestionResult {
  final int questionId;
  final String questionText;
  final String userAnswer;
  final String correctAnswer;
  final bool isCorrect;
  final String? explanation;

  QuestionResult({
    required this.questionId,
    required this.questionText,
    required this.userAnswer,
    required this.correctAnswer,
    required this.isCorrect,
    this.explanation,
  });

  factory QuestionResult.fromJson(Map<String, dynamic> json) {
    return QuestionResult(
      questionId: json['question_id'] as int? ?? 0,
      questionText: json['question_text'] as String? ?? '',
      userAnswer: json['user_answer'] as String? ?? '',
      correctAnswer: json['correct_answer'] as String? ?? '',
      isCorrect: json['is_correct'] as bool? ?? false,
      explanation: json['explanation'] as String?,
    );
  }
}
