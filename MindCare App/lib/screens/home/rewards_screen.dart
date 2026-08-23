import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/rewards/badge_tile.dart';
import '../../widgets/rewards/earn_today_tile.dart';
import '../../widgets/rewards/level_progress_card.dart';
import '../../widgets/rewards/streak_stats_row.dart';

class RewardsScreen extends StatelessWidget {
  const RewardsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 130),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'REWARDS',
                        textAlign: TextAlign.center,
                        style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                      ),
                    ),
                    IconButton(onPressed: () {}, icon: const Icon(Icons.ios_share, size: 18, color: AppColors.textDark)),
                  ],
                ),
                const SizedBox(height: 8),
                LevelProgressCard(
                  levelNumber: provider.levelNumber,
                  levelName: provider.levelName,
                  nextLevelName: provider.nextLevelName,
                  currentPoints: provider.currentPoints,
                  nextLevelPoints: provider.nextLevelPoints,
                ),
                const SizedBox(height: 14),
                StreakStatsRow(
                  streak: provider.checkinStreak,
                  sessions: provider.statsSessions,
                  exercises: provider.statsExercises,
                  journals: provider.statsJournals,
                ),
                const SizedBox(height: 22),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('YOUR BADGES', style: AppTextStyles.label()),
                    Text('${provider.badgesUnlocked} / ${provider.badgesTotal}', style: AppTextStyles.body(size: 13)),
                  ],
                ),
                const SizedBox(height: 12),
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: provider.badges.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 0.95,
                  ),
                  itemBuilder: (context, index) => BadgeTile(badge: provider.badges[index]),
                ),
                const SizedBox(height: 22),
                Text('EARN TODAY', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                ...provider.earnTasks.map((task) => EarnTodayTile(task: task)),
              ],
            ),
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}