import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

import 'package:mindcare_mobile/core/services/api_client.dart';
import 'package:mindcare_mobile/core/services/profile_api.dart';
import 'package:mindcare_mobile/core/utils/validators.dart';
import 'package:mindcare_mobile/models/profile_data.dart';
import 'package:mindcare_mobile/providers/profile_provider.dart';
import 'package:mindcare_mobile/screens/profile/mental_health_history_screen.dart';
import 'package:mindcare_mobile/screens/profile/personal_details_screen.dart';
import 'package:mindcare_mobile/screens/profile/profile_privacy_screen.dart';
import 'package:mindcare_mobile/widgets/profile/complete_profile_card.dart';

class _MemoryTokens implements TokenStore {
  String? accessToken = 'access-1';
  String? refreshToken = 'refresh-1';

  @override
  Future<String?> access() async => accessToken;
  @override
  Future<String?> refresh() async => refreshToken;
  @override
  Future<void> save({required String access, String? refresh}) async {
    accessToken = access;
    if (refresh != null) refreshToken = refresh;
  }

  @override
  Future<void> clear() async {
    accessToken = null;
    refreshToken = null;
  }
}

http.Response _json(Object? body, [int status = 200]) =>
    http.Response.bytes(utf8.encode(jsonEncode(body)), status, headers: {'content-type': 'application/json'});

/// A fake backend with the shapes from the patients and reference serializers.
class _FakeBackend {
  final requests = <String>[];
  final bodies = <String, Object?>{};

  Map<String, dynamic> me = {
    'pseudonym': 'Quiet River 42',
    'full_name': 'Ayesha Khan',
    'is_profile_public': false,
    'photo_url': null,
    'privacy': {
      'shown_when_public': ['full_name', 'photo'],
      'always_private': ['date_of_birth', 'phone_number', 'mental_health_history'],
    },
    'profile_completion': {
      'missing': ['gender', 'phone_number', 'mental_health_history'],
    },
    'country': {'code': 'PK', 'name': 'Pakistan'},
    'city': {'id': 3, 'name': 'Lahore', 'country': 'PK'},
    'timezone': 'Asia/Karachi',
    'date_of_birth': '1998-05-14',
    'gender': '',
    'phone_number': '',
    'preferred_language': {'code': 'ur', 'name': 'Urdu'},
  };

  Map<String, dynamic> history = {
    'concerns': [],
    'previous_diagnosis': null,
    'current_medication': null,
    'previous_therapy': null,
    'notes': '',
    'is_empty': true,
    'updated_at': null,
  };

  MockClient get client => MockClient((req) async {
        final path = req.url.path.replaceFirst(RegExp(r'^.*/api/v1'), '');
        requests.add('${req.method} $path');
        final body = req.body.isEmpty ? null : jsonDecode(req.body);
        if (body != null) bodies['${req.method} $path'] = body;
        switch ('${req.method} $path') {
          case 'GET /patients/me/':
            return _json(me);
          case 'PATCH /patients/me/':
            final changes = body as Map<String, dynamic>;
            if (changes['phone_number'] == 'bad') {
              return _json({'phone_number': [Validators.phoneMessage]}, 400);
            }
            if (changes.containsKey('is_profile_public')) me['is_profile_public'] = changes['is_profile_public'];
            return _json(me);
          case 'GET /patients/me/history/':
            return _json(history);
          case 'PUT /patients/me/history/':
            final b = body as Map<String, dynamic>;
            history = {
              'concerns': [
                for (final slug in b['concerns'] as List) {'slug': slug, 'name': slug == 'anxiety' ? 'Anxiety' : 'Depression'},
              ],
              'previous_diagnosis': b['previous_diagnosis'],
              'current_medication': b['current_medication'],
              'previous_therapy': b['previous_therapy'],
              'notes': b['notes'] ?? '',
              'is_empty': false,
              'updated_at': '2026-10-17T10:00:00Z',
            };
            (me['profile_completion'] as Map)['missing'] = ['gender', 'phone_number'];
            return _json(history);
          case 'DELETE /patients/me/history/':
            return http.Response('', 204);
          case 'GET /reference/countries/':
            return _json([
              {'code': 'PK', 'name': 'Pakistan'},
              {'code': 'GB', 'name': 'United Kingdom'},
            ]);
          case 'GET /reference/languages/':
            return _json([
              {'code': 'en', 'name': 'English'},
              {'code': 'ur', 'name': 'Urdu'},
            ]);
          case 'GET /reference/specializations/':
            return _json([
              {'slug': 'anxiety', 'name': 'Anxiety'},
              {'slug': 'depression', 'name': 'Depression'},
            ]);
        }
        return _json({'detail': 'Not found.'}, 404);
      });
}

ProfileProvider _provider(_FakeBackend backend) =>
    ProfileProvider(ProfileApi(ApiClient(client: backend.client, tokens: _MemoryTokens())));

Widget _wrap(Widget child, ProfileProvider provider) => ChangeNotifierProvider.value(
      value: provider,
      child: MaterialApp(home: Scaffold(body: child)),
    );

void _bigScreen(WidgetTester tester) {
  tester.view.physicalSize = const Size(1500, 4200);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}

void main() {
  group('Validators mirror validation-rules.md', () {
    test('person name', () {
      expect(Validators.personName('Ayesha Khan', label: 'City'), isNull);
      expect(Validators.personName("D'Souza-Ali", label: 'City'), isNull);
      expect(Validators.personName('لاہور', label: 'City'), isNull);
      expect(Validators.personName('Lahore1', label: 'City'), contains('can only contain letters'));
      expect(Validators.personName('A', label: 'City'), 'City must be between 2 and 100 characters.');
      expect(Validators.personName("A.'", label: 'City'), 'City must contain at least 2 letters.');
    });

    test('phone number', () {
      expect(Validators.normalizePhone('0300 123-4567'), '+923001234567');
      expect(Validators.normalizePhone('0044 20 7946 0958'), '+442079460958');
      expect(Validators.phoneNumber('03001234567'), isNull);
      expect(Validators.phoneNumber('+923001234567'), isNull);
      expect(Validators.phoneNumber(''), isNull);
      expect(Validators.phoneNumber('12345'), Validators.phoneMessage);
    });

    test('date of birth', () {
      final today = DateTime(2026, 10, 17);
      expect(Validators.dateOfBirth(DateTime(2008, 10, 17), today: today), isNull);
      expect(Validators.dateOfBirth(DateTime(2008, 10, 18), today: today), 'You must be 18 or older to use MindCare.');
      expect(Validators.dateOfBirth(DateTime(2027, 1, 1), today: today), "Date of birth can't be in the future.");
      expect(Validators.dateOfBirth(DateTime(1900, 1, 1), today: today), 'Enter a real date of birth (age 120 or under).');
    });

    test('free text notes', () {
      String? notes(String v) => Validators.freeText(v, label: 'Notes', min: 10, max: 1000);
      expect(notes(''), isNull);
      expect(notes('short'), 'Notes must be between 10 and 1000 characters.');
      expect(notes('I have <b>panic</b> attacks'), "Notes can't contain HTML tags.");
      expect(notes('1234567890 !!'), 'Notes must contain at least 3 letters.');
      expect(notes('I sleep badly before exams.'), isNull);
    });
  });

  group('ProfileProvider against the fake backend', () {
    test('loads the profile and passes the real name on', () async {
      final backend = _FakeBackend();
      final provider = _provider(backend);
      String? name;
      provider.onName = (n) => name = n;
      await provider.load();

      final p = provider.profile.data!;
      expect(p.pseudonym, 'Quiet River 42');
      expect(p.city!.name, 'Lahore');
      expect(p.language!.code, 'ur');
      expect(p.gender, isNull);
      expect(p.phoneNumber, isNull);
      expect(p.dateOfBirth, DateTime(1998, 5, 14));
      expect(p.missing, ['gender', 'phone_number', 'mental_health_history']);
      expect(name, 'Ayesha Khan');
    });

    test('a 400 comes back with the message under its field', () async {
      final provider = _provider(_FakeBackend());
      final error = await provider.update({'phone_number': 'bad'});
      expect(error!.statusCode, 400);
      expect(error.fieldErrors['phone_number'], Validators.phoneMessage);
      expect(provider.saving, isFalse);
    });

    test('saving history sends the whole history and refreshes what is missing', () async {
      final backend = _FakeBackend();
      final provider = _provider(backend);
      await provider.load();
      final error = await provider.saveHistory(const MentalHealthHistory(
        concerns: [RefItem(code: 'anxiety', name: 'Anxiety')],
        previousTherapy: HistoryAnswer.no,
        notes: 'I sleep badly before exams.',
      ));
      expect(error, isNull);
      expect(backend.bodies['PUT /patients/me/history/'], {
        'concerns': ['anxiety'],
        'previous_diagnosis': null,
        'current_medication': null,
        'previous_therapy': 'no',
        'notes': 'I sleep badly before exams.',
      });
      expect(provider.history.data!.isEmpty, isFalse);
      expect(provider.profile.data!.missing, isNot(contains('mental_health_history')));
    });

    test('reset forgets everything on sign-out', () async {
      final provider = _provider(_FakeBackend());
      await provider.load();
      provider.dismissCompleteCard();
      provider.reset();
      expect(provider.profile.hasData, isFalse);
      expect(provider.completeCardDismissed, isFalse);
    });
  });

  group('Profile screens', () {
    testWidgets('visibility shows the pseudonym and asks before going public', (tester) async {
      _bigScreen(tester);
      final backend = _FakeBackend();
      final provider = _provider(backend);
      await tester.pumpWidget(_wrap(const ProfilePrivacyScreen(), provider));
      await tester.pumpAndSettle();

      expect(find.text('Others see "Quiet River 42"'), findsOneWidget);
      expect(find.text('Your real name'), findsOneWidget);
      expect(find.text('Mental health history'), findsOneWidget);

      await tester.tap(find.byType(Switch));
      await tester.pumpAndSettle();
      expect(find.text('Show your real name?'), findsOneWidget);
      await tester.tap(find.text('Stay private'));
      await tester.pumpAndSettle();
      expect(backend.requests, isNot(contains('PATCH /patients/me/')));

      await tester.tap(find.byType(Switch));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Make public'));
      await tester.pumpAndSettle();
      expect(backend.bodies['PATCH /patients/me/'], {'is_profile_public': true});
      expect(find.text('Others see "Ayesha Khan"'), findsOneWidget);
    });

    testWidgets('personal details checks the phone and sends only what changed', (tester) async {
      _bigScreen(tester);
      final backend = _FakeBackend();
      final provider = _provider(backend);
      await tester.pumpWidget(_wrap(const PersonalDetailsScreen(), provider));
      await tester.pumpAndSettle();

      expect(find.text('Ayesha Khan'), findsOneWidget);
      expect(find.text('Shown to others as Quiet River 42'), findsOneWidget);
      expect(find.text('Saved'), findsOneWidget);

      final phone = find.widgetWithText(TextField, '03001234567 or +923001234567');
      await tester.enterText(phone, '12345');
      await tester.pump();
      expect(find.text(Validators.phoneMessage), findsOneWidget);

      await tester.enterText(phone, '0300 1234567');
      await tester.tap(find.text('Female'));
      await tester.pump();
      expect(find.text(Validators.phoneMessage), findsNothing);
      await tester.tap(find.text('Save changes'));
      await tester.pumpAndSettle();

      expect(backend.bodies['PATCH /patients/me/'], {'gender': 'female', 'phone_number': '0300 1234567'});
    });

    testWidgets('history: pick concerns and answers, then save', (tester) async {
      _bigScreen(tester);
      final backend = _FakeBackend();
      final provider = _provider(backend);
      await tester.pumpWidget(_wrap(const MentalHealthHistoryScreen(), provider));
      await tester.pumpAndSettle();

      expect(find.textContaining('only you and your current psychologist'), findsOneWidget);
      expect(find.text('Delete my history'), findsNothing);
      // Therapy has no "prefer not to say": two of the three questions do.
      expect(find.text('Prefer not to say'), findsNWidgets(2));

      await tester.tap(find.text('Anxiety'));
      await tester.tap(find.text('Yes').first);
      await tester.enterText(find.byType(TextField), 'short');
      await tester.pump();
      expect(find.text('Notes must be between 10 and 1000 characters.'), findsOneWidget);

      await tester.enterText(find.byType(TextField), 'I sleep badly before exams.');
      await tester.pump();
      await tester.tap(find.text('Save history'));
      await tester.pumpAndSettle();

      expect(backend.bodies['PUT /patients/me/history/'], {
        'concerns': ['anxiety'],
        'previous_diagnosis': 'yes',
        'current_medication': null,
        'previous_therapy': null,
        'notes': 'I sleep badly before exams.',
      });
      expect(find.text('Delete my history'), findsOneWidget);
    });

    testWidgets('complete-your-profile card lists what is empty and can be skipped', (tester) async {
      _bigScreen(tester);
      final provider = _provider(_FakeBackend());
      await tester.pumpWidget(_wrap(const CompleteProfileCard(), provider));
      await tester.pumpAndSettle();

      expect(find.text('Complete your profile'), findsOneWidget);
      expect(find.text('4 of 7'), findsOneWidget);
      expect(find.textContaining('Gender, Phone number, Mental health history'), findsOneWidget);

      await tester.tap(find.text('Not now'));
      await tester.pump();
      expect(find.text('Complete your profile'), findsNothing);
    });
  });
}
