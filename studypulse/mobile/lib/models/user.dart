class User {
  final int id;
  final String username;
  final String email;
  final String? fullName;
  final bool isGuest;
  final DateTime? createdAt;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.fullName,
    this.isGuest = false,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      username: json['username'] as String? ?? '',
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String?,
      isGuest: json['is_guest'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'full_name': fullName,
      'is_guest': isGuest,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}
