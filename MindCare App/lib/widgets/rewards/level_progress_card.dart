import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class LevelProgressCard extends StatelessWidget {
  const LevelProgressCard({
    super.key,
    required this.levelNumber,
    required this.levelName,
    required this.nextLevelName,
    required this.currentPoints,
    required this.nextLevelPoints,
  });

  final int levelNumber;
  final String levelName;
  final String nextLevelName;
  final int currentPoints;
  final int nextLevelPoints;

  @override
  Widget build(BuildContext context) {
    final progress = (currentPoints / nextLevelPoints).clamp(0.0, 1.0);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFFF0DEB9), Color(0xFFEDE6D2)], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('LEVEL $levelNumber', style: AppTextStyles.label()),
          const SizedBox(height: 4),
          Text(levelName, style: AppTextStyles.heading(size: 32, style: FontStyle.italic)),
          const SizedBox(height: 8),
          RichText(
            text: TextSpan(
              style: AppTextStyles.body(size: 14),
              children: [
                const TextSpan(text: 'Two more sessions to reach '),
                TextSpan(text: nextLevelName, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                const TextSpan(text: '.'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: Colors.white.withOpacity(0.5),
              valueColor: const AlwaysStoppedAnimation(AppColors.amberSegment),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('$currentPoints pts', style: AppTextStyles.body(size: 12)),
              Text('$nextLevelPoints pts', style: AppTextStyles.body(size: 12)),
            ],
          ),
        ],
      ),
    );
  }
}