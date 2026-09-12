import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class UpcomingChargeCard extends StatelessWidget {
  const UpcomingChargeCard({super.key, required this.charge});
  final Map<String, dynamic> charge;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: charge['therapistColor'] as Color,
            child: Text(charge['therapistInitials'] as String, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(charge['title'] as String, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                const SizedBox(height: 2),
                Text(charge['subtitle'] as String, style: AppTextStyles.body(size: 12)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(charge['amount'] as String, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
              Text(charge['note'] as String, style: AppTextStyles.body(size: 11)),
            ],
          ),
        ],
      ),
    );
  }
}