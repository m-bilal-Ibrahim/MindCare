import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/account_data.dart';

class BadgeTile extends StatelessWidget {
  const BadgeTile({super.key, required this.badge});
  final RewardBadge badge;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: badge.unlocked
                  ? RadialGradient(colors: [badge.iconColor.withOpacity(0.9), badge.iconColor])
                  : null,
              color: badge.unlocked ? null : const Color(0xFFEFE9DA),
            ),
            child: Icon(badge.icon, color: badge.unlocked ? Colors.white : const Color(0xFFB8AF9C), size: 22),
          ),
          const SizedBox(height: 10),
          Text(
            badge.name,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: badge.unlocked ? AppColors.textDark : AppColors.textMuted),
          ),
        ],
      ),
    );
  }
}