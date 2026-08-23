import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class MoodOption {
  const MoodOption(this.label, this.color);
  final String label;
  final Color color;
}

class MoodCard extends StatelessWidget {
  const MoodCard({super.key, required this.option, required this.selected, required this.onTap});
  final MoodOption option;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: AppColors.cardBackground,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? AppColors.textDark : AppColors.border, width: selected ? 1.6 : 1),
        ),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Column(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(colors: [option.color.withOpacity(0.9), option.color]),
                  ),
                ),
                const SizedBox(height: 10),
                Text(option.label, style: const TextStyle(fontWeight: FontWeight.w500, color: AppColors.textDark)),
              ],
            ),
            if (selected)
              Positioned(
                top: -8,
                right: 4,
                child: Container(
                  width: 20,
                  height: 20,
                  decoration: const BoxDecoration(color: AppColors.textDark, shape: BoxShape.circle),
                  child: const Icon(Icons.check, size: 13, color: Colors.white),
                ),
              ),
          ],
        ),
      ),
    );
  }
}