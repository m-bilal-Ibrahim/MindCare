import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/account_data.dart';

class EarnTodayTile extends StatelessWidget {
  const EarnTodayTile({super.key, required this.task});
  final EarnTask task;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: task.done ? const Color(0xFFDCEAE2) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: task.done ? null : Border.all(color: AppColors.border, width: 1.5),
            ),
            child: task.done ? const Icon(Icons.check, size: 16, color: AppColors.progressActive) : null,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(task.title, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                const SizedBox(height: 2),
                Text(task.subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
            child: Text('+${task.points}', style: const TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w700, fontSize: 12)),
          ),
        ],
      ),
    );
  }
}