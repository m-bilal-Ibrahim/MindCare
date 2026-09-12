import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/checkin_provider.dart';

class MoodSelector extends StatelessWidget {
  const MoodSelector({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CheckinProvider>();
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: CheckinProvider.dailyMoods.map((mood) {
        final selected = provider.selectedDailyMoodId == mood.id;
        return GestureDetector(
          onTap: () => context.read<CheckinProvider>().selectDailyMood(mood.id),
          child: Column(
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(colors: [mood.color.withOpacity(0.9), mood.color]),
                  border: selected ? Border.all(color: AppColors.textDark, width: 2) : null,
                  boxShadow: selected
                      ? [BoxShadow(color: mood.color.withOpacity(0.4), blurRadius: 10, spreadRadius: 1)]
                      : null,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                mood.label,
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textDark,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}