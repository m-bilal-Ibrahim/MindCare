import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class DayChip extends StatelessWidget {
  const DayChip({super.key, required this.label, required this.date, required this.selected, required this.onTap});
  final String label;
  final int date;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 56,
        padding: const EdgeInsets.symmetric(vertical: 12),
        margin: const EdgeInsets.only(right: 8),
        decoration: BoxDecoration(
          color: selected ? AppColors.textDark : Colors.white,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          children: [
            Text(label, style: TextStyle(fontSize: 12, color: selected ? Colors.white70 : AppColors.textMuted)),
            const SizedBox(height: 4),
            Text(
              '$date',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: selected ? Colors.white : AppColors.textDark),
            ),
          ],
        ),
      ),
    );
  }
}