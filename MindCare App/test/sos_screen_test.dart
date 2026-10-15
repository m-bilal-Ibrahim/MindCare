import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mindcare_mobile/core/constants/emergency_numbers.dart';
import 'package:mindcare_mobile/screens/sos/sos_screen.dart';

void main() {
  testWidgets('SOS shows only the fixed emergency numbers', (tester) async {
    tester.view.physicalSize = const Size(1500, 4200);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(const MaterialApp(home: SosScreen()));

    for (final n in emergencyNumbers) {
      expect(find.text(n.name), findsOneWidget);
    }
    expect(find.text('Rescue 1122'), findsOneWidget);
    expect(find.text('1122'), findsOneWidget);

    // Nothing without a backend yet.
    expect(find.textContaining('Notify your circle'), findsNothing);
    expect(find.textContaining('Nearby hospitals'), findsNothing);
    expect(find.textContaining('Aida'), findsNothing);
  });
}
