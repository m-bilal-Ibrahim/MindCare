import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../models/account_data.dart';

class UpcomingChargeCard extends StatelessWidget {
  const UpcomingChargeCard({super.key, required this.charge});

  /// Null when nothing is scheduled.
  final WalletCharge? charge;

  @override
  Widget build(BuildContext context) {
    final c = charge;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: c == null
          ? Row(
              children: [
                const Icon(Icons.event_available_outlined, size: 20, color: AppColors.textMuted),
                const SizedBox(width: 12),
                Expanded(child: Text('No upcoming charges.', style: AppTextStyles.body(size: 13))),
              ],
            )
          : Row(
              children: [
                CircleAvatar(
                  radius: 22,
                  backgroundColor: c.color ?? AppColors.progressActive,
                  child: c.initials == null
                      ? const Icon(Icons.receipt_long_outlined, color: Colors.white, size: 18)
                      : Text(c.initials!, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(c.title, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                      const SizedBox(height: 2),
                      Text(c.subtitle, style: AppTextStyles.body(size: 12)),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(c.amount, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                    if (c.note != null) Text(c.note!, style: AppTextStyles.body(size: 11)),
                  ],
                ),
              ],
            ),
    );
  }
}
