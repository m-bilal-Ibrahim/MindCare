import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/program_data.dart';

class FeaturedAudioCard extends StatelessWidget {
  const FeaturedAudioCard({
    super.key,
    required this.track,
    required this.position,
    required this.isPlaying,
    required this.onPlayToggle,
  });

  final AudioTrack track;
  final String position;
  final bool isPlaying;
  final VoidCallback onPlayToggle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [AppColors.audioCardStart, AppColors.audioCardEnd], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(track.tag, style: const TextStyle(color: Colors.white70, fontSize: 11, letterSpacing: 1, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(track.title, style: const TextStyle(color: Colors.white, fontSize: 22, fontFamily: 'serif')),
          const SizedBox(height: 14),
          if (track.arabic != null)
            Align(
              alignment: Alignment.centerRight,
              child: Text(track.arabic!, textDirection: TextDirection.rtl, style: const TextStyle(color: Colors.white, fontSize: 22, height: 1.6)),
            ),
          const SizedBox(height: 10),
          Text(track.translation, style: const TextStyle(color: Colors.white70, fontSize: 13, fontStyle: FontStyle.italic)),
          const SizedBox(height: 20),
          Row(
            children: [
              GestureDetector(
                onTap: onPlayToggle,
                child: Container(
                  width: 46,
                  height: 46,
                  decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                  child: Icon(isPlaying ? Icons.pause : Icons.play_arrow, color: AppColors.audioCardEnd, size: 24),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(child: SizedBox(height: 24, child: _Waveform())),
              const SizedBox(width: 10),
              Text('$position / ${track.duration}', style: const TextStyle(color: Colors.white70, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }
}

class _Waveform extends StatelessWidget {
  static const _heights = [6, 12, 18, 10, 16, 22, 14, 9, 18, 12, 20, 8, 15, 11, 19, 13, 7, 16, 10, 14];

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: List.generate(_heights.length, (i) {
        final played = i < 8;
        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 1.2),
            height: _heights[i].toDouble(),
            decoration: BoxDecoration(
              color: played ? Colors.white : Colors.white.withOpacity(0.3),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        );
      }),
    );
  }
}