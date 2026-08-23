import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class WaterCard extends StatelessWidget {
  const WaterCard({super.key, required this.filled, required this.total});
  final int filled;
  final int total;

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
                decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(9)),
                child: const Icon(Icons.water_drop_outlined, size: 14, color: AppColors.textDark),
              ),
              const SizedBox(width: 8),
              Text('WATER', style: AppTextStyles.label()),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: List.generate(total, (i) {
              final isFilled = i < filled;
              return Container(
                width: 20,
                height: 26,
                decoration: BoxDecoration(
                  color: isFilled ? AppColors.progressActive : AppColors.background,
                  borderRadius: BorderRadius.circular(6),
                ),
              );
            }),
          ),
          const SizedBox(height: 10),
          Text('$filled / $total glasses', style: AppTextStyles.body(size: 12)),
        ],
      ),
    );
  }
}