import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../models/program_data.dart';

class SmallStepTile extends StatelessWidget {
  const SmallStepTile({super.key, required this.step, this.showDivider = true, this.onTap});
  final DailyStep step;
  final bool showDivider;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        InkWell(
          onTap: onTap,
          child: Padding(
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
                    // Done is shown by the tick alone; the text stays readable.
                    style: const TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          ),
        ),
        if (showDivider) const Divider(height: 1, color: AppColors.border, indent: 16, endIndent: 16),
      ],
    );
  }
}
