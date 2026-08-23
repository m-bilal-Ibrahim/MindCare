import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/program_data.dart';

class SmallStepTile extends StatelessWidget {
  const SmallStepTile({super.key, required this.step, this.showDivider = true});
  final DailyStep step;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
          child: Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: step.done ? AppColors.progressActive : Colors.transparent,
                  borderRadius: BorderRadius.circular(7),
                  border: step.done ? null : Border.all(color: AppColors.border, width: 1.5),
                ),
                child: step.done ? const Icon(Icons.check, size: 15, color: Colors.white) : null,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  step.label,
                  style: TextStyle(
                    color: step.done ? AppColors.textMuted : AppColors.textDark,
                    decoration: step.done ? TextDecoration.lineThrough : TextDecoration.none,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1, color: AppColors.border, indent: 16, endIndent: 16),
      ],
    );
  }
}