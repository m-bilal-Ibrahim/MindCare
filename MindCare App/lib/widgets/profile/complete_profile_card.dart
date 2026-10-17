import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../models/profile_data.dart';
import '../../providers/profile_provider.dart';
import '../../screens/profile/mental_health_history_screen.dart';
import '../../screens/profile/personal_details_screen.dart';

/// Loads the profile once and, while optional parts are still empty, offers
/// to fill them in. "Not now" hides it until the next sign-in.
class CompleteProfileCard extends StatefulWidget {
  const CompleteProfileCard({super.key});

  @override
  State<CompleteProfileCard> createState() => _CompleteProfileCardState();
}

class _CompleteProfileCardState extends State<CompleteProfileCard> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<ProfileProvider>().ensureLoaded();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProfileProvider>();
    final missing = provider.profile.data?.missing ?? const <String>[];
    if (missing.isEmpty || provider.completeCardDismissed) return const SizedBox.shrink();

    final onlyHistory = missing.length == 1 && missing.first == 'mental_health_history';
    final labels = missing.map((m) => profilePartLabels[m] ?? m).toList();
    final total = profilePartLabels.length;
    final done = (total - missing.length).clamp(0, total);

    return Container(
      margin: const EdgeInsets.only(bottom: 22),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text('Complete your profile', style: AppTextStyles.heading(size: 19))),
              Text('$done of $total', style: AppTextStyles.body(size: 12)),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: done / total,
              minHeight: 6,
              backgroundColor: Colors.white,
              color: AppColors.progressActive,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Optional, but it helps your psychologist. Still empty: ${labels.join(', ')}.',
            style: AppTextStyles.body(size: 13),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              ElevatedButton(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => MobileFrame(child: onlyHistory ? const MentalHealthHistoryScreen() : const PersonalDetailsScreen()),
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryDark,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('Fill in', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
              ),
              const SizedBox(width: 8),
              TextButton(
                onPressed: provider.dismissCompleteCard,
                child: const Text('Not now', style: TextStyle(color: AppColors.textMuted)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
