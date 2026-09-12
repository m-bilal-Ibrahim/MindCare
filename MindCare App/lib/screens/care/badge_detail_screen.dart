import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../models/account_data.dart';

class BadgeDetailScreen extends StatelessWidget {
  const BadgeDetailScreen({super.key, required this.badge});
  final RewardBadge badge;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                  ),
                  const Spacer(),
                ],
              ),
              const SizedBox(height: 20),
              Container(
                width: 110,
                height: 110,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: badge.unlocked
                      ? RadialGradient(colors: [badge.iconColor.withOpacity(0.9), badge.iconColor])
                      : null,
                  color: badge.unlocked ? null : const Color(0xFFEFE9DA),
                ),
                child: Icon(badge.icon, color: badge.unlocked ? Colors.white : const Color(0xFFB8AF9C), size: 44),
              ),
              const SizedBox(height: 20),
              Text(badge.name, style: AppTextStyles.heading(size: 26)),
              const SizedBox(height: 8),
              if (badge.unlocked && badge.unlockedDate != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
                  child: Text('Unlocked ${badge.unlockedDate}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.progressActive)),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: const Color(0xFFEFE9DA), borderRadius: BorderRadius.circular(20)),
                  child: const Text('Locked', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textMuted)),
                ),
              const SizedBox(height: 24),
              Text(badge.description, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: AppColors.textDark, height: 1.5)),
              const SizedBox(height: 24),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                child: Row(
                  children: [
                    Icon(badge.unlocked ? Icons.check_circle_outline : Icons.flag_outlined, size: 18, color: AppColors.textDark),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('HOW TO EARN IT', style: TextStyle(fontSize: 10, letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          Text(badge.criteria, style: const TextStyle(fontSize: 13, color: AppColors.textDark, fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}