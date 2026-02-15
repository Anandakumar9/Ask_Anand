class Exam {
  final int id;
  final String name;
  final String? description;
  final String? icon;
  final List<Subject> subjects;

  Exam({
    required this.id,
    required this.name,
    this.description,
    this.icon,
    this.subjects = const [],
  });

  factory Exam.fromJson(Map<String, dynamic> json) {
    return Exam(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      icon: json['icon'] as String?,
      subjects: (json['subjects'] as List<dynamic>?)
              ?.map((s) => Subject.fromJson(s as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class Subject {
  final int id;
  final String name;
  final String? description;
  final int examId;
  final List<Topic> topics;

  Subject({
    required this.id,
    required this.name,
    this.description,
    required this.examId,
    this.topics = const [],
  });

  factory Subject.fromJson(Map<String, dynamic> json) {
    return Subject(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      examId: json['exam_id'] as int? ?? 0,
      topics: (json['topics'] as List<dynamic>?)
              ?.map((t) => Topic.fromJson(t as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class Topic {
  final int id;
  final String name;
  final String? description;
  final int subjectId;
  final int? questionCount;

  Topic({
    required this.id,
    required this.name,
    this.description,
    required this.subjectId,
    this.questionCount,
  });

  factory Topic.fromJson(Map<String, dynamic> json) {
    return Topic(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      subjectId: json['subject_id'] as int? ?? 0,
      questionCount: json['question_count'] as int?,
    );
  }
}
