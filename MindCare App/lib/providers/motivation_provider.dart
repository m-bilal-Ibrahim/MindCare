import 'package:flutter/material.dart';

import '../core/services/api_client.dart';
import '../core/services/motivation_api.dart';
import '../models/motivation_data.dart';

/// One piece of server data and how loading it went.
class Loadable<T> {
  const Loadable({this.data, this.loading = false, this.error, this.sessionExpired = false});

  final T? data;
  final bool loading;
  final String? error;
  final bool sessionExpired;

  bool get hasData => data != null;
}

/// Motivation Corner: quotes for everyone; Quran and duas only for
/// patients who turn them on (they're off by default, never pre-selected).
class MotivationProvider extends ChangeNotifier {
  MotivationProvider([MotivationApi? api]) : _api = api ?? MotivationApi();

  final MotivationApi _api;

  static const List<String> tabs = ['Quotes', 'Duas', 'Surahs'];
  String selectedTab = 'Quotes';

  void selectTab(String tab) {
    selectedTab = tab;
    notifyListeners();
    if (tab != 'Quotes' && optIn.data == null && !optIn.loading) loadOptIn();
    if (tab == 'Duas' && optIn.data == true && !duas.hasData) loadDuas();
    if (tab == 'Surahs' && optIn.data == true && !surahs.hasData) loadSurahs();
  }

  // ----- Quote of the moment -----
  Loadable<Quote?> quoteOfMoment = const Loadable();

  Future<void> loadQuoteOfMoment() async {
    quoteOfMoment = Loadable(data: quoteOfMoment.data, loading: true);
    notifyListeners();
    try {
      final quote = await _api.randomQuote();
      quoteOfMoment = Loadable(data: quote);
    } on ApiException catch (e) {
      quoteOfMoment = Loadable(data: quoteOfMoment.data, error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  // ----- Quotes list -----
  QuoteCategory? category;
  List<Quote> quotes = const [];
  int quotesTotal = 0;
  int _page = 0;
  bool quotesHasMore = true;
  bool quotesLoading = false;
  String? quotesError;
  bool quotesLoaded = false;

  void setCategory(QuoteCategory? value) {
    if (category == value) return;
    category = value;
    loadQuotes(reset: true);
  }

  Future<void> loadQuotes({bool reset = false}) async {
    if (quotesLoading) return;
    if (reset) {
      quotes = const [];
      _page = 0;
      quotesHasMore = true;
      quotesLoaded = false;
    }
    if (!quotesHasMore) return;
    quotesLoading = true;
    quotesError = null;
    notifyListeners();
    final requested = category;
    try {
      final page = await _api.quotes(category: requested, page: _page + 1);
      if (requested != category) return; // the filter changed while loading
      _page++;
      quotes = [...quotes, ...page.quotes];
      quotesTotal = page.total;
      quotesHasMore = page.hasMore;
      quotesLoaded = true;
    } on ApiException catch (e) {
      quotesError = e.message;
      _sessionExpired = e.isSessionExpired;
    } finally {
      quotesLoading = false;
      notifyListeners();
    }
  }

  // ----- Quran and duas opt-in -----
  Loadable<bool> optIn = const Loadable();
  bool savingOptIn = false;

  Future<void> loadOptIn() async {
    optIn = const Loadable(loading: true);
    notifyListeners();
    try {
      optIn = Loadable(data: await _api.religiousOptIn());
    } on ApiException catch (e) {
      optIn = Loadable(error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  /// Returns an error message, or null on success.
  Future<String?> setOptIn(bool value) async {
    savingOptIn = true;
    notifyListeners();
    try {
      final now = await _api.setReligiousOptIn(value);
      optIn = Loadable(data: now);
      if (!now) {
        duas = const Loadable();
        surahs = const Loadable();
      } else {
        if (selectedTab == 'Duas') loadDuas();
        if (selectedTab == 'Surahs') loadSurahs();
      }
      return null;
    } on ApiException catch (e) {
      _sessionExpired = e.isSessionExpired;
      return e.message;
    } finally {
      savingOptIn = false;
      notifyListeners();
    }
  }

  // ----- Duas and surahs -----
  Loadable<List<Dua>> duas = const Loadable();
  Loadable<List<SurahSummary>> surahs = const Loadable();

  Future<void> loadDuas() async {
    duas = const Loadable(loading: true);
    notifyListeners();
    try {
      duas = Loadable(data: await _api.duas());
    } on ApiException catch (e) {
      if (e.statusCode == 403) optIn = const Loadable(data: false);
      duas = Loadable(error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  Future<void> loadSurahs() async {
    surahs = const Loadable(loading: true);
    notifyListeners();
    try {
      surahs = Loadable(data: await _api.surahs());
    } on ApiException catch (e) {
      if (e.statusCode == 403) optIn = const Loadable(data: false);
      surahs = Loadable(error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  Future<Dua> dua(int id) => _api.dua(id);

  Future<Surah> surah(int number) => _api.surah(number);

  bool _sessionExpired = false;

  /// True once any call found the sign-in has ended.
  bool get sessionExpired =>
      _sessionExpired || quoteOfMoment.sessionExpired || optIn.sessionExpired || duas.sessionExpired || surahs.sessionExpired;

  /// Forget everything on sign-out, so the next person starts fresh.
  void reset() {
    selectedTab = 'Quotes';
    quoteOfMoment = const Loadable();
    category = null;
    quotes = const [];
    quotesTotal = 0;
    _page = 0;
    quotesHasMore = true;
    quotesLoading = false;
    quotesError = null;
    quotesLoaded = false;
    optIn = const Loadable();
    duas = const Loadable();
    surahs = const Loadable();
    _sessionExpired = false;
    notifyListeners();
  }

  /// First visit to the screen.
  void start() {
    if (!quoteOfMoment.hasData && !quoteOfMoment.loading) loadQuoteOfMoment();
    if (!quotesLoaded && !quotesLoading) loadQuotes(reset: true);
  }
}
