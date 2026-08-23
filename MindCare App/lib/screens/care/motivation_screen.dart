import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/program_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/motivation/audio_list_item.dart';
import '../../widgets/motivation/featured_audio_card.dart';
import '../../widgets/motivation/motivation_tab_bar.dart';

class MotivationScreen extends StatelessWidget {
  const MotivationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProgramProvider>();

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [AppColors.motivationBgStart, AppColors.motivationBgEnd], begin: Alignment.topCenter, end: Alignment.bottomCenter),
        ),
        child: SafeArea(
          child: Stack(
            children: [
              ListView(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
                children: [
                  Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.chevron_left, color: Colors.white),
                      ),
                      const Expanded(
                        child: Text(
                          'MOTIVATION',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: Colors.white70, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      IconButton(onPressed: () {}, icon: const Icon(Icons.bookmark_border, color: Colors.white)),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Text('Today', textAlign: TextAlign.center, style: TextStyle(color: Colors.white60, fontFamily: 'serif', fontStyle: FontStyle.italic, fontSize: 18)),
                  const SizedBox(height: 12),
                  Text(
                    '"${provider.todayQuote}"',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif', height: 1.3),
                  ),
                  const SizedBox(height: 12),
                  Text(provider.todayQuoteReference, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54, fontSize: 12, letterSpacing: 1)),
                  const SizedBox(height: 24),
                  MotivationTabBar(
                    tabs: ProgramProvider.motivationTabs,
                    selected: provider.selectedMotivationTab,
                    onChanged: (tab) => context.read<ProgramProvider>().setMotivationTab(tab),
                  ),
                  const SizedBox(height: 22),
                  FeaturedAudioCard(
                    track: provider.featuredTrack,
                    position: provider.featuredPosition,
                    isPlaying: provider.featuredPlaying,
                    onPlayToggle: () => context.read<ProgramProvider>().toggleFeaturedPlayback(),
                  ),
                  const SizedBox(height: 24),
                  const Text('MORE FOR WHAT YOU\'RE CARRYING', style: TextStyle(color: Colors.white54, fontSize: 11, letterSpacing: 1, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  ...provider.moreTracks.map((track) => AudioListItem(track: track)),
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