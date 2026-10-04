import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mindcare_mobile/core/services/auth_api.dart';

String _jwt(Map<String, dynamic> claims) {
  String part(Map<String, dynamic> m) => base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
  return '${part({'alg': 'HS256'})}.${part(claims)}.sig';
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // In-memory stand-in for flutter_secure_storage's platform channel.
  final store = <String, String>{};
  setUp(() {
    store.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
      (call) async {
        final args = (call.arguments as Map?) ?? {};
        switch (call.method) {
          case 'write':
            store[args['key'] as String] = args['value'] as String;
          case 'read':
            return store[args['key']];
          case 'deleteAll':
            store.clear();
        }
        return null;
      },
    );
  });

  group('registerPatient', () {
    test('sends the exact patient contract', () async {
      late Map<String, dynamic> sent;
      late http.Request request;
      final api = AuthApi.withClient(MockClient((req) async {
        request = req;
        sent = jsonDecode(req.body) as Map<String, dynamic>;
        return http.Response('{"id": 1}', 201);
      }));

      await api.registerPatient(
        email: 'ayesha@example.com',
        password: 'Str0ng-pass-2026',
        fullName: 'Ayesha Khan',
        isAdultConfirmed: true,
      );

      expect(request.url.toString(), '${AuthApi.baseUrl}/accounts/register/');
      expect(request.headers['Content-Type'], startsWith('application/json'));
      expect(sent.keys.toSet(), {'email', 'password', 'full_name', 'role', 'is_adult_confirmed', 'profile'});
      expect(sent['role'], 'patient');
      // Must be the JSON boolean, not "true" or 1.
      expect(sent['is_adult_confirmed'], same(true));
      expect((sent['profile'] as Map).keys, ['timezone']);
      expect(sent.containsKey('date_of_birth'), isFalse);
    });

    test('maps field errors, including nested profile errors', () async {
      final api = AuthApi.withClient(MockClient((_) async => http.Response(
            jsonEncode({
              'email': ['A user with this email already exists.'],
              'is_adult_confirmed': ['You must confirm you are 18 or older.'],
              'profile': {
                'timezone': ['Unknown timezone.'],
              },
            }),
            400,
          )));

      await expectLater(
        api.registerPatient(email: 'a@b.co', password: 'x', fullName: 'A', isAdultConfirmed: true),
        throwsA(isA<AuthException>()
            .having((e) => e.fieldErrors['email'], 'email', 'A user with this email already exists.')
            .having((e) => e.fieldErrors['is_adult_confirmed'], 'adult', 'You must confirm you are 18 or older.')
            .having((e) => e.fieldErrors['profile.timezone'], 'timezone', 'Unknown timezone.')),
      );
    });

    test('reports network failures without crashing', () async {
      final api = AuthApi.withClient(MockClient((_) => throw http.ClientException('offline')));
      await expectLater(
        api.registerPatient(email: 'a@b.co', password: 'x', fullName: 'A', isAdultConfirmed: true),
        throwsA(isA<AuthException>().having((e) => e.message, 'message', contains("Couldn't reach"))),
      );
    });
  });

  group('login', () {
    test('stores tokens for a patient', () async {
      final access = _jwt({'role': 'patient'});
      final api = AuthApi.withClient(MockClient((req) async {
        expect(req.url.path, endsWith('/accounts/login/'));
        return http.Response(jsonEncode({'access': access, 'refresh': 'r-token'}), 200);
      }));

      final role = await api.login(email: 'a@b.co', password: 'pw');

      expect(role, 'patient');
      expect(store['auth_token'], access);
      expect(store['refresh_token'], 'r-token');
    });

    test('turns away psychologist and NGO accounts without storing tokens', () async {
      final api = AuthApi.withClient(MockClient((_) async =>
          http.Response(jsonEncode({'access': _jwt({'role': 'psychologist'}), 'refresh': 'r'}), 200)));

      await expectLater(api.login(email: 'a@b.co', password: 'pw'), throwsA(isA<AuthException>()));
      expect(store, isEmpty);
    });

    test('surfaces the backend detail message on bad credentials', () async {
      final api = AuthApi.withClient(MockClient((_) async =>
          http.Response(jsonEncode({'detail': 'No active account found with the given credentials'}), 401)));

      await expectLater(
        api.login(email: 'a@b.co', password: 'wrong'),
        throwsA(isA<AuthException>()
            .having((e) => e.message, 'message', 'No active account found with the given credentials')),
      );
    });
  });
}
