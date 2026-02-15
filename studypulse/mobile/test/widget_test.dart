// Basic Flutter widget smoke test for StudyPulse app.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('StudyPulse app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const StudyPulseApp());

    // Verify that the app builds and renders the title.
    expect(find.text('StudyPulse'), findsWidgets);
  });
}
