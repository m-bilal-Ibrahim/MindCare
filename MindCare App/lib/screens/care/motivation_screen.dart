import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/program_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/motivation/audio_list_item.dart';
import '../../widgets/motivation/featured_audio_card.dart';
import '../../widgets/motivation/motivation_tab_bar.dart';

/// Motivation Corner. The quote, duas and surahs come from the backend;
/// until they do, the screen says so instead of showing placeholder content.
class MotivationScreen extends StatelessWidget {
  const MotivationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProgramProvider>();
    final featured = provider.featuredTrack;
    final featuredBookmarked = featured != null && provider.isTrackBookmarked(featured.id);

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
                      if (featured != null)
                        IconButton(
                          onPressed: () {
                            context.read<ProgramProvider>().toggleTrackBookmark(featured.id);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(featuredBookmarked ? 'Removed from saved' : 'Saved · "${featured.title}"')),
                            );
                          },
                          icon: Icon(featuredBookmarked ? Icons.bookmark : Icons.bookmark_border, color: Colors.white),
                        )
                      else
                        const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Text('Today', textAlign: TextAlign.center, style: TextStyle(color: Colors.white60, fontFamily: 'serif', fontStyle: FontStyle.italic, fontSize: 18)),
                  const SizedBox(height: 12),
                  if (provider.todayQuote != null) ...[
                    Text(
                      '"${provider.todayQuote}"',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif', height: 1.3),
                    ),
                    if (provider.todayQuoteReference != null) ...[
                      const SizedBox(height: 12),
                      Text(provider.todayQuoteReference!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white54, fontSize: 12, letterSpacing: 1)),
                    ],
                  ] else
                    const Text(
                      "Today's words will appear here.",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white70, fontSize: 20, fontFamily: 'serif', height: 1.3),
                    ),
                  const SizedBox(height: 24),
                  MotivationTabBar(
                    tabs: ProgramProvider.motivationTabs,
                    selected: provider.selectedMotivationTab,
                    onChanged: (tab) => context.read<ProgramProvider>().setMotivationTab(tab),
                  ),
                  const SizedBox(height: 22),
                  if (featured == null && provider.moreTracks.isEmpty)
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 30, horizontal: 24),
                      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(22)),
                      child: const Column(
                        children: [
                          Icon(Icons.headphones_outlined, color: Colors.white70, size: 30),
                          SizedBox(height: 12),
                          Text('Nothing here yet', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
                          SizedBox(height: 6),
                          Text(
                            'Duas and surahs with audio will appear here once they are added.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
                          ),
                        ],
                      ),
                    )
                  else ...[
                    if (featured != null)
                      FeaturedAudioCard(
                        track: featured,
                        position: '0:00',
                        isPlaying: provider.isPlaying(featured.id),
                        onPlayToggle: () => context.read<ProgramProvider>().togglePlay(featured.id),
                      ),
                    if (provider.moreTracks.isNotEmpty) ...[
                      const SizedBox(height: 24),
                      const Text("MORE FOR WHAT YOU'RE CARRYING", style: TextStyle(color: Colors.white54, fontSize: 11, letterSpacing: 1, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      ...provider.moreTracks.map((track) {
                        return AudioListItem(
                          track: track,
                          isPlaying: provider.isPlaying(track.id),
                          onTap: () => context.read<ProgramProvider>().togglePlay(track.id),
                        );
                      }),
                    ],
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
}
