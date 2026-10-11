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
    final color = option.color;
    // A lighter tint of the mood colour gives the orb a soft, lit-from-above look.
    final highlight = Color.lerp(color, Colors.white, 0.45)!;

    return Semantics(
      button: true,
      selected: selected,
      label: option.label,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
          decoration: BoxDecoration(
            color: selected ? Color.alphaBlend(color.withValues(alpha: 0.08), AppColors.cardBackground) : AppColors.cardBackground,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: selected ? color : AppColors.border, width: selected ? 1.6 : 1),
          ),
          child: Stack(
            children: [
              Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [highlight, color],
                        ),
                        boxShadow: [
                          BoxShadow(color: color.withValues(alpha: 0.28), blurRadius: 12, offset: const Offset(0, 4)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      option.label,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.textDark),
                    ),
                  ],
                ),
              ),
              Positioned(
                top: 8,
                right: 8,
                child: AnimatedScale(
                  scale: selected ? 1 : 0,
                  duration: const Duration(milliseconds: 180),
                  curve: Curves.easeOutBack,
                  child: Container(
                    width: 20,
                    height: 20,
                    decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                    child: const Icon(Icons.check, size: 13, color: Colors.white),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
