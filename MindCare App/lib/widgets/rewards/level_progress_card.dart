import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class LevelProgressCard extends StatelessWidget {
  const LevelProgressCard({
    super.key,
    required this.levelNumber,
    required this.currentPoints,
    required this.nextLevelPoints,
  });

  final int levelNumber;
  final int currentPoints;

  /// Null until the rewards rules come from the backend.
  final int? nextLevelPoints;

  @override
  Widget build(BuildContext context) {
    final goal = nextLevelPoints;
    final progress = goal == null || goal <= 0 ? 0.0 : (currentPoints / goal).clamp(0.0, 1.0);
    final toGo = goal == null ? null : (goal - currentPoints).clamp(0, goal);

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
          Text('$currentPoints points', style: AppTextStyles.heading(size: 32, style: FontStyle.italic)),
          const SizedBox(height: 8),
          Text(
            currentPoints == 0
                ? 'Check in, do an exercise or write in your journal to start earning points.'
                : toGo == null
                    ? 'Keep going. Every check-in counts.'
                    : '$toGo more points to reach level ${levelNumber + 1}.',
            style: AppTextStyles.body(size: 14),
          ),
          if (goal != null) ...[
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 8,
                backgroundColor: Colors.white.withValues(alpha: 0.5),
                valueColor: const AlwaysStoppedAnimation(AppColors.amberSegment),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('$currentPoints pts', style: AppTextStyles.body(size: 12)),
                Text('$goal pts', style: AppTextStyles.body(size: 12)),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
