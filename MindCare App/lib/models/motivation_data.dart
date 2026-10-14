// Motivation Corner content as the backend sends it (6.10).

enum QuoteCategory {
  hope('hope', 'Hope'),
  resilience('resilience', 'Resilience'),
  calm('calm', 'Calm'),
  selfCare('self_care', 'Self-care');

  const QuoteCategory(this.api, this.label);
  final String api;
  final String label;

  static QuoteCategory? fromApi(String? value) {
    for (final c in values) {
      if (c.api == value) return c;
    }
    return null;
  }
}

class Quote {
  const Quote({required this.id, required this.text, this.author, this.category});

  final int id;
  final String text;
  final String? author;
  final QuoteCategory? category;

  factory Quote.fromJson(Map<String, dynamic> j) => Quote(
        id: j['id'] as int,
        text: j['text'] as String? ?? '',
        author: j['author'] as String?,
        category: QuoteCategory.fromApi(j['category'] as String?),
      );
}

class QuotePage {
  const QuotePage({required this.quotes, required this.total, required this.hasMore});
  final List<Quote> quotes;
  final int total;
  final bool hasMore;
}

class Dua {
  const Dua({
    required this.id,
    required this.title,
    required this.reference,
    required this.arabic,
    required this.translation,
    this.transliteration,
    this.audioUrl,
  });

  final int id;
  final String title;
  final String reference;
  final String arabic;
  final String? transliteration;
  final String translation;

  /// Signed link that works for about five minutes; null when there is no
  /// recitation. Fetch the dua again right before playing.
  final String? audioUrl;

  bool get hasAudio => audioUrl != null;

  factory Dua.fromJson(Map<String, dynamic> j) => Dua(
        id: j['id'] as int,
        title: j['title'] as String? ?? '',
        reference: j['reference'] as String? ?? '',
        arabic: j['arabic'] as String? ?? '',
        transliteration: j['transliteration'] as String?,
        translation: j['translation'] as String? ?? '',
        audioUrl: j['audio_url'] as String?,
      );
}

class SurahSummary {
  const SurahSummary({
    required this.number,
    required this.nameArabic,
    required this.nameEnglish,
    required this.nameMeaning,
    required this.ayahCount,
    required this.hasAudio,
  });

  final int number;
  final String nameArabic;
  final String nameEnglish;
  final String nameMeaning;
  final int ayahCount;
  final bool hasAudio;

  factory SurahSummary.fromJson(Map<String, dynamic> j) => SurahSummary(
        number: j['number'] as int,
        nameArabic: j['name_arabic'] as String? ?? '',
        nameEnglish: j['name_english'] as String? ?? '',
        nameMeaning: j['name_meaning'] as String? ?? '',
        ayahCount: j['ayah_count'] as int? ?? 0,
        hasAudio: j['has_audio'] as bool? ?? false,
      );
}

class Surah {
  const Surah({
    required this.summary,
    required this.arabic,
    required this.translation,
    this.transliteration,
    this.audioUrl,
  });

  final SurahSummary summary;

  /// One verse per line.
  final String arabic;
  final String? transliteration;
  final String translation;
  final String? audioUrl;

  List<String> get arabicVerses => _lines(arabic);
  List<String> get translationVerses => _lines(translation);
  List<String> get transliterationVerses => transliteration == null ? const [] : _lines(transliteration!);

  static List<String> _lines(String text) => text.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();

  factory Surah.fromJson(Map<String, dynamic> j) => Surah(
        summary: SurahSummary.fromJson({...j, 'has_audio': j['audio_url'] != null}),
        arabic: j['arabic'] as String? ?? '',
        transliteration: j['transliteration'] as String?,
        translation: j['translation'] as String? ?? '',
        audioUrl: j['audio_url'] as String?,
      );
}
