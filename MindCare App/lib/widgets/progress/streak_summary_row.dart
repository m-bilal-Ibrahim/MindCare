import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class StreakSummaryRow extends StatelessWidget {
  const StreakSummaryRow({
    super.key,
    required this.streakDays,
    required this.avgMood,
    required this.avgMoodDelta,
  });

  final int streakDays;
  final double avgMood;
  final double avgMoodDelta;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          flex: 6,
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle),
                      child: const Icon(Icons.local_fire_department, color: Colors.white, size: 18),
                    ),
                    const SizedBox(width: 10),
                    Text('$streakDays days', style: AppTextStyles.heading(size: 20)),
                  ],
                ),
                const SizedBox(height: 2),
                Padding(
                  padding: const EdgeInsets.only(left: 44),
                  child: Text('check-in streak', style: AppTextStyles.body(size: 12)),
                ),
                const SizedBox(height: 14),
                Row(
                  children: List.generate(streakDays.clamp(0, 14), (i) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 4),
                      child: Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle),
                      ),
                    );
                  }),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 5,
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('AVG MOOD', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(avgMood.toStringAsFixed(1), style: AppTextStyles.heading(size: 26)),
                    Text(' /5', style: AppTextStyles.body(size: 13)),
                  ],
                ),
                const SizedBox(height: 6),
                Text('↑ ${avgMoodDelta.toStringAsFixed(1)} vs last month', style: AppTextStyles.body(size: 12)),
              ],
            ),
          ),
        ),
      ],
    );
  }
}