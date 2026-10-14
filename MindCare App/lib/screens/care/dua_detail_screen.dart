import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../models/motivation_data.dart';
import '../../providers/motivation_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/motivation/motivation_states.dart';
import '../../widgets/motivation/recitation_player.dart';

/// One dua: Arabic (right to left), transliteration, translation, and the
/// recitation when there is one.
class DuaDetailScreen extends StatelessWidget {
  const DuaDetailScreen({super.key, required this.dua});
  final Dua dua;

  @override
  Widget build(BuildContext context) {
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
                      const Expanded(
                        child: Text(
                          'DUA',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: Colors.white70, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(dua.title, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif')),
                  const SizedBox(height: 6),
                  Text(dua.reference, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54, fontSize: 12, letterSpacing: 0.8)),
                  const SizedBox(height: 24),
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [AppColors.audioCardStart, AppColors.audioCardEnd], begin: Alignment.topLeft, end: Alignment.bottomRight),
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(dua.arabic, textDirection: TextDirection.rtl, textAlign: TextAlign.right, style: arabicStyle(size: 26)),
                        if (dua.transliteration != null) ...[
                          const SizedBox(height: 14),
                          Text(dua.transliteration!, style: const TextStyle(color: Colors.white70, fontSize: 14, fontStyle: FontStyle.italic, height: 1.5)),
                        ],
                        const SizedBox(height: 14),
                        Text(dua.translation, style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.5)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  if (dua.hasAudio)
                    RecitationPlayer(
                      // Re-fetch for a fresh signed link (they last ~5 minutes).
                      fetchUrl: () async => (await context.read<MotivationProvider>().dua(dua.id)).audioUrl,
                    )
                  else
                    const Text('No recitation for this dua yet.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white54, fontSize: 12)),
                  const SizedBox(height: 18),
                  const Text(quranAttribution, textAlign: TextAlign.center, style: TextStyle(color: Colors.white38, fontSize: 11, height: 1.4)),
                ],
              ),
              const Positioned(right: 0, bottom: 24, child: SosButton()),
            ],
          ),
        ),
      ),
    );
  }
}
