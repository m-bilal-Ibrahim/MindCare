import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class StepProgressBar extends StatelessWidget {
  const StepProgressBar({super.key, required this.currentStep, required this.totalSteps});
  final int currentStep;
  final int totalSteps;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Row(
            children: List.generate(totalSteps, (index) {
              final isActive = index < currentStep;
              return Expanded(
                child: Container(
                  margin: EdgeInsets.only(right: index == totalSteps - 1 ? 0 : 8),
                  height: 4,
                  decoration: BoxDecoration(
                    color: isActive ? AppColors.progressActive : AppColors.progressTrack,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              );
            }),
          ),
        ),
        const SizedBox(width: 12),
        Text('$currentStep / $totalSteps', style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
      ],
    );
  }
}