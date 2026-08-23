import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/checkin_data.dart';

class InsightTile extends StatelessWidget {
  const InsightTile({super.key, required this.insight});
  final ProgressInsight insight;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(color: insight.iconBackground, borderRadius: BorderRadius.circular(12)),
            child: Icon(insight.icon, size: 18, color: AppColors.textDark),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(insight.title, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                const SizedBox(height: 4),
                Text(insight.description, style: const TextStyle(fontSize: 13, color: AppColors.textMuted, height: 1.35)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}