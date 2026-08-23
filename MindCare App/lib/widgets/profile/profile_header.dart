import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class ProfileHeader extends StatelessWidget {
  const ProfileHeader({
    super.key,
    required this.name,
    required this.joinedInfo,
    required this.levelBadge,
    required this.streak,
    required this.sessions,
    required this.exercises,
  });

  final String name;
  final String joinedInfo;
  final String levelBadge;
  final int streak;
  final int sessions;
  final int exercises;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const CircleAvatar(radius: 34, backgroundColor: Color(0xFFE5382B), child: Text('LS', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18))),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: AppTextStyles.heading(size: 24)),
                  const SizedBox(height: 4),
                  Text(joinedInfo, style: AppTextStyles.body(size: 13)),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(color: const Color(0xFFF0DEB9), borderRadius: BorderRadius.circular(20)),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.stars, size: 13, color: AppColors.textDark),
                        const SizedBox(width: 5),
                        Text(levelBadge, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textDark)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(child: _StatPill(value: '${streak}d', label: 'streak')),
            const SizedBox(width: 10),
            Expanded(child: _StatPill(value: '$sessions', label: 'sessions')),
            const SizedBox(width: 10),
            Expanded(child: _StatPill(value: '$exercises', label: 'exercises')),
          ],
        ),
      ],
    );
  }
}

class _StatPill extends StatelessWidget {
  const _StatPill({required this.value, required this.label});
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
      child: Column(
        children: [
          Text(value, style: AppTextStyles.heading(size: 22)),
          const SizedBox(height: 2),
          Text(label, style: AppTextStyles.body(size: 12)),
        ],
      ),
    );
  }
}