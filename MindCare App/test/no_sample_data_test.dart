import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:mindcare_mobile/models/checkin_data.dart';
import 'package:mindcare_mobile/models/program_data.dart';
import 'package:mindcare_mobile/providers/account_provider.dart';
import 'package:mindcare_mobile/providers/checkin_provider.dart';
import 'package:mindcare_mobile/providers/community_provider.dart';
import 'package:mindcare_mobile/providers/notifications_provider.dart';
import 'package:mindcare_mobile/providers/onboarding_provider.dart';
import 'package:mindcare_mobile/providers/program_provider.dart';
import 'package:mindcare_mobile/providers/settings_provider.dart';
import 'package:mindcare_mobile/providers/therapy_provider.dart';
import 'package:mindcare_mobile/providers/user_session_provider.dart';
import 'package:mindcare_mobile/screens/care/browse_therapists_screen.dart';
import 'package:mindcare_mobile/screens/care/wellbeing_view.dart';
import 'package:mindcare_mobile/screens/home/aida_chat_screen.dart';
import 'package:mindcare_mobile/screens/home/progress_screen.dart';
import 'package:mindcare_mobile/screens/home/rewards_screen.dart';
import 'package:mindcare_mobile/screens/home/wallet_screen.dart';
import 'package:mindcare_mobile/widgets/care/small_step_tile.dart';

Widget _wrap(Widget child, {CheckinProvider? checkin, ProgramProvider? program}) => MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => UserSessionProvider()..setName('Test Patient')),
        ChangeNotifierProvider(create: (_) => OnboardingProvider()),
        ChangeNotifierProvider(create: (_) => checkin ?? CheckinProvider()),
        ChangeNotifierProvider(create: (_) => TherapyProvider()),
        ChangeNotifierProvider(create: (_) => program ?? ProgramProvider()),
        ChangeNotifierProvider(create: (_) => CommunityProvider()),
        ChangeNotifierProvider(create: (_) => AccountProvider()),
        ChangeNotifierProvider(create: (_) => NotificationsProvider()),
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
      ],
      child: MaterialApp(home: Scaffold(body: child)),
    );

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(1500, 4500);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}

void main() {
  testWidgets('Wellbeing shows empty states, not sample numbers', (tester) async {
    _phone(tester);
    await tester.pumpWidget(_wrap(const WellbeingView()));
    await tester.pump();

    expect(find.text('6,612'), findsNothing);
    expect(find.text('7h 38m today'), findsNothing);
    expect(find.text('No readings today'), findsOneWidget);
    expect(find.text('Nothing logged yet'), findsNWidgets(2)); // meals and water
    expect(find.textContaining('No small steps yet'), findsOneWidget);
    expect(find.textContaining('Tip:'), findsNothing);
  });

  testWidgets('Steps and calm time come from sensor readings', (tester) async {
    _phone(tester);
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, now.day, 0, 1);
    final checkin = CheckinProvider()
      ..addReadings([
        VitalReading(at: start, heartRate: 70, breathingRate: 14, steps: 300),
        VitalReading(at: start.add(const Duration(minutes: 10)), heartRate: 110, breathingRate: 22, steps: 900),
        VitalReading(at: start.add(const Duration(minutes: 20)), heartRate: 72, breathingRate: 14, steps: 1500),
      ]);

    await tester.pumpWidget(_wrap(const WellbeingView(), checkin: checkin));
    await tester.pump();

    expect(find.text('1,500'), findsOneWidget);
    expect(find.text('67%'), findsOneWidget); // 2 of 3 readings calm
    expect(find.textContaining('m today'), findsOneWidget);
  });

  test('calm time counts calm readings and caps long gaps', () {
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, now.day, 0, 1);
    final p = CheckinProvider()
      ..addReadings([
        VitalReading(at: start, heartRate: 70, breathingRate: 14),
        VitalReading(at: start.add(const Duration(minutes: 5)), heartRate: 120, breathingRate: 25),
        VitalReading(at: start.add(const Duration(minutes: 10)), heartRate: 70, breathingRate: 14),
        VitalReading(at: start.add(const Duration(hours: 3)), heartRate: 70, breathingRate: 14),
      ]);
    final calm = p.calmToday!;
    // 5 min (first reading) + 15 min cap (third reading's long gap) + up to 15 min (last reading)
    expect(calm.calm.inMinutes, inInclusiveRange(20, 35));
    expect(calm.share, 0.75);
  });

  testWidgets('A finished small step shows a tick and readable text', (tester) async {
    await tester.pumpWidget(_wrap(const SmallStepTile(step: DailyStep('Stretch for 5 minutes', true))));
    final text = tester.widget<Text>(find.text('Stretch for 5 minutes'));
    expect(text.style?.decoration, isNot(TextDecoration.lineThrough));
    expect(find.byIcon(Icons.check), findsOneWidget);
  });

  testWidgets('Small steps can be ticked once the care plan has them', (tester) async {
    _phone(tester);
    final program = ProgramProvider()..setSmallSteps(const [DailyStep('Sunlight before 10 AM', false)]);
    await tester.pumpWidget(_wrap(const WellbeingView(), program: program));
    await tester.tap(find.text('Sunlight before 10 AM'));
    await tester.pump();
    expect(program.smallSteps.single.done, isTrue);
  });

  testWidgets('Care tab, wallet, rewards and progress start empty', (tester) async {
    _phone(tester);
    await tester.pumpWidget(_wrap(const BrowseTherapistsScreen()));
    await tester.pump();
    expect(find.text('No psychologists listed yet'), findsOneWidget);
    expect(find.textContaining('Tariq'), findsNothing);

    await tester.pumpWidget(_wrap(const WalletScreen()));
    await tester.pump();
    expect(find.text('No transactions yet.'), findsOneWidget);
    expect(find.text('No saved cards yet.'), findsOneWidget);
    expect(find.text('No upcoming charges.'), findsOneWidget);

    await tester.pumpWidget(_wrap(const RewardsScreen()));
    await tester.pump();
    expect(find.text('0 points'), findsOneWidget);
    expect(find.text('0 / 6'), findsOneWidget);

    await tester.pumpWidget(_wrap(const ProgressScreen()));
    await tester.pump();
    expect(find.text('Your progress starts here.'), findsOneWidget);
  });

  testWidgets('Aida starts with an introduction, not a scripted chat', (tester) async {
    _phone(tester);
    final checkin = CheckinProvider();
    await tester.pumpWidget(_wrap(const AidaChatScreen(), checkin: checkin));
    await tester.pump();

    expect(find.text("Hi Test, I'm Aida."), findsOneWidget);
    expect(checkin.messages, isEmpty);

    await checkin.sendMessage('Hello');
    expect(checkin.messages.last.text, CheckinProvider.notConnectedReply);
  });
}
