import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../models/motivation_data.dart';
import '../../providers/motivation_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/motivation/motivation_states.dart';
import '../../widgets/motivation/recitation_player.dart';

/// A surah, verse by verse: Arabic (right to left) with its translation
/// beneath, plus the recitation when there is one.
class SurahReaderScreen extends StatefulWidget {
  const SurahReaderScreen({super.key, required this.summary});
  final SurahSummary summary;

  @override
  State<SurahReaderScreen> createState() => _SurahReaderScreenState();
}

class _SurahReaderScreenState extends State<SurahReaderScreen> {
  Surah? _surah;
  String? _error;
  bool _sessionExpired = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _error = null;
      _surah = null;
    });
    try {
      final surah = await context.read<MotivationProvider>().surah(widget.summary.number);
      if (mounted) setState(() => _surah = surah);
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _sessionExpired = e.isSessionExpired;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.summary;
    final surah = _surah;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [AppColors.motivationBgStart, AppColors.motivationBgEnd], begin: Alignment.topCenter, end: Alignment.bottomCenter),
        ),
        child: SafeArea(
          child: Stack(
            children: [
              ListView(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 110),
                children: [
                  Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.chevron_left, color: Colors.white),
                      ),
                      Expanded(
                        child: Text(
                          'SURAH ${s.number}',
                          textAlign: TextAlign.center,
                          style: const TextStyle(letterSpacing: 1, color: Colors.white70, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(s.nameArabic, textAlign: TextAlign.center, textDirection: TextDirection.rtl, style: arabicStyle(size: 30)),
                  Text(s.nameEnglish, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 24, fontFamily: 'serif')),
                  const SizedBox(height: 4),
                  Text(
                    '${s.nameMeaning} · ${s.ayahCount} ${s.ayahCount == 1 ? 'verse' : 'verses'}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                  const SizedBox(height: 20),
                  if (surah == null && _error == null)
                    const MotivationLoading(label: 'Loading the surah…')
                  else if (_error != null)
                    MotivationError(message: _error!, sessionExpired: _sessionExpired, onRetry: _load)
                  else ...[
                    if (surah!.audioUrl != null) ...[
                      RecitationPlayer(
                        fetchUrl: () async => (await context.read<MotivationProvider>().surah(s.number)).audioUrl,
                      ),
                      const SizedBox(height: 18),
                    ],
                    ..._verses(surah),
                    const SizedBox(height: 12),
                    const Text(quranAttribution, textAlign: TextAlign.center, style: TextStyle(color: Colors.white38, fontSize: 11, height: 1.4)),
                  ],
                ],
              ),
              const Positioned(right: 0, bottom: 24, child: SosButton()),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _verses(Surah surah) {
    final arabic = surah.arabicVerses;
    final english = surah.translationVerses;
    final translit = surah.transliterationVerses;
    final count = arabic.length > english.length ? arabic.length : english.length;
    return [
      for (var i = 0; i < count; i++)
        Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(18)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    width: 26,
                    height: 26,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), shape: BoxShape.circle),
                    child: Text('${i + 1}', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                  ),
                  const SizedBox(width: 10),
                  if (i < arabic.length)
                    Expanded(
                      child: Text(arabic[i], textDirection: TextDirection.rtl, textAlign: TextAlign.right, style: arabicStyle(size: 22)),
                    ),
                ],
              ),
              if (i < translit.length) ...[
                const SizedBox(height: 8),
                Text(translit[i], style: const TextStyle(color: Colors.white60, fontSize: 13, fontStyle: FontStyle.italic, height: 1.45)),
              ],
              if (i < english.length) ...[
                const SizedBox(height: 8),
                Text(english[i], style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.5)),
              ],
            ],
          ),
        ),
    ];
  }
}
