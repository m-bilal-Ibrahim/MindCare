import 'package:flutter/material.dart';
import '../../models/program_data.dart';

class AudioListItem extends StatelessWidget {
  const AudioListItem({super.key, required this.track, required this.isPlaying, required this.onTap});
  final AudioTrack track;
  final bool isPlaying;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isPlaying ? Colors.white.withOpacity(0.16) : Colors.white.withOpacity(0.08),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: Colors.white.withOpacity(0.14), shape: BoxShape.circle),
              child: Icon(isPlaying ? Icons.pause : Icons.play_arrow, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(track.title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                  if (track.translation.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(track.translation, style: const TextStyle(color: Colors.white60, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(track.duration, style: const TextStyle(color: Colors.white70, fontSize: 12)),
                if (track.tag.isNotEmpty) Text(track.tag, style: const TextStyle(color: Colors.white38, fontSize: 10)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}