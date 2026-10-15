import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

import 'package:mindcare_mobile/core/services/api_client.dart';
import 'package:mindcare_mobile/core/services/motivation_api.dart';
import 'package:mindcare_mobile/models/motivation_data.dart';
import 'package:mindcare_mobile/providers/motivation_provider.dart';
import 'package:mindcare_mobile/screens/care/motivation_screen.dart';
import 'package:mindcare_mobile/screens/care/surah_reader_screen.dart';
import 'package:mindcare_mobile/widgets/common/skeleton.dart';

class _MemoryTokens implements TokenStore {
  _MemoryTokens();
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

/// JSON with no charset, like the backend sends, so UTF-8 handling is tested.
http.Response _json(Object body, [int status = 200]) =>
    http.Response.bytes(utf8.encode(jsonEncode(body)), status, headers: {'content-type': 'application/json'});

const _dua = {
  'id': 1,
  'title': 'Dua of Yunus',
  'reference': 'Quran 21:87',
  'arabic': 'لَا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ',
  'transliteration': null,
  'translation': 'There is no God save Thee. Be Thou glorified!',
  'audio_url': 'https://storage.example/dua1.mp3?sig=1',
};

/// A fake backend for the Motivation Corner, using the shapes from the
/// backend serializers.
class _FakeBackend {
  bool optedIn = false;
  final requests = <String>[];

  MockClient get client => MockClient((req) async {
        requests.add('${req.method} ${req.url.path}${req.url.hasQuery ? '?${req.url.query}' : ''}');
        final path = req.url.path.replaceFirst(RegExp(r'^.*/api/v1'), '');
        switch (path) {
          case '/motivation/quotes/random/':
            return _json({'id': 7, 'text': 'Small steps still move you forward.', 'author': 'MindCare', 'category': 'hope'});
          case '/motivation/quotes/':
            final cat = req.url.queryParameters['category'];
            final all = [
              {'id': 1, 'text': 'Rest is not quitting, it is preparing.', 'author': null, 'category': 'self_care'},
              {'id': 2, 'text': 'You have survived every hard day so far.', 'author': 'Unknown', 'category': 'resilience'},
            ];
            final results = cat == null ? all : all.where((q) => q['category'] == cat).toList();
            return _json({'count': results.length, 'next': null, 'previous': null, 'results': results});
          case '/motivation/religious/preference/':
            if (req.method == 'PUT') optedIn = (jsonDecode(req.body) as Map)['opted_in'] == true;
            return _json({'opted_in': optedIn});
          case '/motivation/duas/':
            if (!optedIn) return _json({'detail': 'Turn on Quran and dua content in your Motivation Corner settings to see this.'}, 403);
            return _json([_dua]);
          case '/motivation/surahs/':
            if (!optedIn) return _json({'detail': 'Turn on Quran and dua content.'}, 403);
            return _json([
              {'number': 112, 'name_arabic': 'الإخلاص', 'name_english': 'Al-Ikhlas', 'name_meaning': 'Sincerity', 'ayah_count': 4, 'has_audio': false},
            ]);
          case '/motivation/surahs/112/':
            return _json({
              'number': 112,
              'name_arabic': 'الإخلاص',
              'name_english': 'Al-Ikhlas',
              'name_meaning': 'Sincerity',
              'ayah_count': 2,
              'arabic': 'قُلْ هُوَ اللَّهُ أَحَدٌ\nاللَّهُ الصَّمَدُ',
              'transliteration': null,
              'translation': 'Say: He is Allah, the One!\nAllah, the eternally Besought of all!',
              'audio_url': null,
            });
        }
        return _json({'detail': 'Not found.'}, 404);
      });
}

Widget _wrap(Widget child, MotivationProvider provider) => ChangeNotifierProvider.value(
      value: provider,
      child: MaterialApp(home: child),
    );

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(1500, 4200);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}

void main() {
  group('ApiClient', () {
    test('refreshes once on 401, saves the rotated tokens and retries', () async {
      final tokens = _MemoryTokens();
      var calls = 0;
      final client = MockClient((req) async {
        if (req.url.path.endsWith('/accounts/refresh/')) {
          expect(jsonDecode(req.body), {'refresh': 'refresh-1'});
          return _json({'access': 'access-2', 'refresh': 'refresh-2'});
        }
        calls++;
        if (req.headers['Authorization'] == 'Bearer access-1') return _json({'detail': 'expired'}, 401);
        expect(req.headers['Authorization'], 'Bearer access-2');
        return _json({'opted_in': false});
      });
      final api = ApiClient(client: client, tokens: tokens);

      expect(await api.get('/motivation/religious/preference/'), {'opted_in': false});
      expect(calls, 2);
      expect(tokens.accessToken, 'access-2');
      expect(tokens.refreshToken, 'refresh-2');
    });

    test('a failed refresh clears the tokens and reports the session ended', () async {
      final tokens = _MemoryTokens();
      final client = MockClient((req) async => _json({'detail': 'Token is invalid'}, 401));
      final api = ApiClient(client: client, tokens: tokens);

      await expectLater(
        api.get('/motivation/quotes/'),
        throwsA(isA<ApiException>().having((e) => e.isSessionExpired, 'sessionExpired', isTrue)),
      );
      expect(tokens.accessToken, isNull);
    });

    test('backend messages come through for 403 and a friendly one for 429', () {
      expect(ApiException.fromResponse(403, {'detail': 'Turn on Quran and dua content.'}).message, 'Turn on Quran and dua content.');
      expect(ApiException.fromResponse(429, {'detail': 'Request was throttled.'}).message, startsWith('Too many attempts'));
    });
  });

  group('MotivationApi', () {
    test('parses Arabic text intact from a response without a charset', () async {
      final backend = _FakeBackend()..optedIn = true;
      final api = MotivationApi(ApiClient(client: backend.client, tokens: _MemoryTokens()));
      final duas = await api.duas();
      expect(duas.single.arabic, _dua['arabic']);
      expect(duas.single.hasAudio, isTrue);
    });

    test('quotes send the category filter and read the page', () async {
      final backend = _FakeBackend();
      final api = MotivationApi(ApiClient(client: backend.client, tokens: _MemoryTokens()));
      final page = await api.quotes(category: QuoteCategory.selfCare);
      expect(backend.requests.last, contains('category=self_care'));
      expect(page.quotes.single.category, QuoteCategory.selfCare);
      expect(page.quotes.single.author, isNull);
      expect(page.hasMore, isFalse);
    });

    test('surah verses are split one per line', () {
      final surah = Surah.fromJson({
        'number': 1,
        'name_arabic': 'x',
        'name_english': 'y',
        'name_meaning': 'z',
        'ayah_count': 2,
        'arabic': 'a\nb\n',
        'translation': 'A\nB',
        'transliteration': null,
        'audio_url': null,
      });
      expect(surah.arabicVerses, ['a', 'b']);
      expect(surah.translationVerses, ['A', 'B']);
      expect(surah.summary.hasAudio, isFalse);
    });
  });

  testWidgets('Motivation shows the real quote and quotes, then duas after opting in', (tester) async {
    _phone(tester);
    final backend = _FakeBackend();
    final provider = MotivationProvider(MotivationApi(ApiClient(client: backend.client, tokens: _MemoryTokens())));

    await tester.pumpWidget(_wrap(const MotivationScreen(), provider));
    await tester.pumpAndSettle();

    expect(find.text('“Small steps still move you forward.”'), findsOneWidget);
    expect(find.text('“Rest is not quitting, it is preparing.”'), findsOneWidget);

    await tester.tap(find.text('Resilience').first);
    await tester.pumpAndSettle();
    expect(find.text('“Rest is not quitting, it is preparing.”'), findsNothing);
    expect(find.text('“You have survived every hard day so far.”'), findsOneWidget);

    // Duas are off by default and never pre-selected.
    await tester.tap(find.text('Duas'));
    await tester.pumpAndSettle();
    expect(find.text('Show Quran and duas'), findsOneWidget);
    expect(backend.optedIn, isFalse);

    await tester.tap(find.text('Show Quran and duas'));
    await tester.pumpAndSettle();
    expect(backend.optedIn, isTrue);
    expect(find.text('Dua of Yunus'), findsOneWidget);
    expect(find.text('Quran 21:87'), findsOneWidget);
  });

  testWidgets('Surah reader shows each verse with its translation', (tester) async {
    _phone(tester);
    final backend = _FakeBackend()..optedIn = true;
    final provider = MotivationProvider(MotivationApi(ApiClient(client: backend.client, tokens: _MemoryTokens())));
    const summary = SurahSummary(number: 112, nameArabic: 'الإخلاص', nameEnglish: 'Al-Ikhlas', nameMeaning: 'Sincerity', ayahCount: 2, hasAudio: false);

    await tester.pumpWidget(_wrap(const SurahReaderScreen(summary: summary), provider));
    await tester.pumpAndSettle();

    expect(find.text('Say: He is Allah, the One!'), findsOneWidget);
    expect(find.text('Allah, the eternally Besought of all!'), findsOneWidget);
    expect(find.text('اللَّهُ الصَّمَدُ'), findsOneWidget);
    expect(find.byIcon(Icons.play_arrow), findsNothing); // no recitation yet
  });

  testWidgets('While loading, pages show skeletons instead of spinners', (tester) async {
    _phone(tester);
    final gate = Completer<void>();
    final backend = _FakeBackend();
    final fast = backend.client;
    final slow = MockClient((req) async {
      await gate.future;
      final copy = http.Request(req.method, req.url)..headers.addAll(req.headers);
      return http.Response.fromStream(await fast.send(copy));
    });
    final provider = MotivationProvider(MotivationApi(ApiClient(client: slow, tokens: _MemoryTokens())));

    await tester.pumpWidget(_wrap(const MotivationScreen(), provider));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byType(Shimmer), findsWidgets);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    gate.complete();
    await tester.pumpAndSettle();
    expect(find.byType(Shimmer), findsNothing);
    expect(find.text('“Small steps still move you forward.”'), findsOneWidget);
  });
}
