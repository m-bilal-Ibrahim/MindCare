import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class StreakStatsRow extends StatelessWidget {
  const StreakStatsRow({
    super.key,
    required this.streak,
    required this.sessions,
    required this.exercises,
    required this.journals,
  });

  final int streak;
  final int sessions;
  final int exercises;
  final int journals;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          flex: 4,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle),
                  child: const Icon(Icons.local_fire_department, color: Colors.white, size: 16),
                ),
                const SizedBox(height: 10),
                Text('${streak}d', style: AppTextStyles.heading(size: 24)),
                Text('check-in\nstreak', style: AppTextStyles.body(size: 12)),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 6,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('STATS', style: AppTextStyles.label()),
                    Text('30d', style: AppTextStyles.body(size: 11)),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(child: _Stat(value: sessions, label: 'sessions')),
                    Expanded(child: _Stat(value: exercises, label: 'exercises')),
                    Expanded(child: _Stat(value: journals, label: 'journals')),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label});
  final int value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('$value', style: AppTextStyles.heading(size: 22)),
        Text(label, style: AppTextStyles.body(size: 11)),
      ],
    );
  }
}