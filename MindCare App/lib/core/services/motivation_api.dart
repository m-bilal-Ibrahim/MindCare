import '../../models/motivation_data.dart';
import 'api_client.dart';

/// Motivation Corner endpoints (backend handoff: motivation-corner.md).
class MotivationApi {
  MotivationApi([ApiClient? client]) : _api = client ?? ApiClient.instance;

  final ApiClient _api;

  /// One random quote, or null when there are none (404).
  Future<Quote?> randomQuote({QuoteCategory? category}) async {
    try {
      final body = await _api.get('/motivation/quotes/random/', query: {if (category != null) 'category': category.api});
      return body is Map<String, dynamic> ? Quote.fromJson(body) : null;
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<QuotePage> quotes({QuoteCategory? category, int page = 1}) async {
    final body = await _api.get('/motivation/quotes/', query: {
      'page': '$page',
      if (category != null) 'category': category.api,
    });
    final map = body is Map<String, dynamic> ? body : const <String, dynamic>{};
    final results = (map['results'] as List? ?? const []).whereType<Map<String, dynamic>>().map(Quote.fromJson).toList();
    return QuotePage(quotes: results, total: map['count'] as int? ?? results.length, hasMore: map['next'] != null);
  }

  Future<bool> religiousOptIn() async {
    final body = await _api.get('/motivation/religious/preference/');
    return body is Map<String, dynamic> && body['opted_in'] == true;
  }

  /// Turning it off deletes the patient's opt-in on the server.
  Future<bool> setReligiousOptIn(bool optedIn) async {
    final body = await _api.put('/motivation/religious/preference/', {'opted_in': optedIn});
    return body is Map<String, dynamic> && body['opted_in'] == true;
  }

  Future<List<Dua>> duas() async {
    final body = await _api.get('/motivation/duas/');
    return (body as List? ?? const []).whereType<Map<String, dynamic>>().map(Dua.fromJson).toList();
  }

  /// Fetched right before playing, for a fresh audio link.
  Future<Dua> dua(int id) async => Dua.fromJson(await _api.get('/motivation/duas/$id/') as Map<String, dynamic>);

  Future<List<SurahSummary>> surahs() async {
    final body = await _api.get('/motivation/surahs/');
    return (body as List? ?? const []).whereType<Map<String, dynamic>>().map(SurahSummary.fromJson).toList();
  }

  Future<Surah> surah(int number) async => Surah.fromJson(await _api.get('/motivation/surahs/$number/') as Map<String, dynamic>);
}
