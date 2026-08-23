import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class MealsCard extends StatelessWidget {
  const MealsCard({super.key, required this.mealsDone, required this.dinnerTime});
  final List<bool> mealsDone;
  final String dinnerTime;

  static const _labels = ['B', 'L', 'S', 'D'];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(color: const Color(0xFFF0DEB9), borderRadius: BorderRadius.circular(9)),
                child: const Icon(Icons.restaurant, size: 14, color: AppColors.textDark),
              ),
              const SizedBox(width: 8),
              Text('MEALS', style: AppTextStyles.label()),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: List.generate(_labels.length, (i) {
              final done = mealsDone[i];
              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: i == _labels.length - 1 ? 0 : 6),
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: Container(
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: done ? const Color(0xFFDCEAE2) : AppColors.background,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        _labels[i],
                        style: TextStyle(fontWeight: FontWeight.w700, color: done ? AppColors.progressActive : AppColors.textMuted),
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 10),
          Text(dinnerTime, style: AppTextStyles.body(size: 12)),
        ],
      ),
    );
  }
}