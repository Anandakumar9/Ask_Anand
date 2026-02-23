import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'screens/welcome_screen_exam.dart';
import 'store/app_store.dart';
import 'store/app_theme.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppStore()),
      ],
      child: const StudyPulseApp(),
    ),
  );
}

class StudyPulseApp extends StatelessWidget {
  const StudyPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStore>(
      builder: (context, appStore, child) {
        return MaterialApp(
          title: 'StudyPulse',
          debugShowCheckedModeBanner: false,
          themeMode: appStore.themeMode,
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          home: const WelcomeScreenExam(),
        );
      },
    );
  }
}

