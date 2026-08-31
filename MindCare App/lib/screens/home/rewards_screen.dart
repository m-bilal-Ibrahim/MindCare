import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/share_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/rewards/badge_tile.dart';
import '../../widgets/rewards/earn_today_tile.dart';
import '../../widgets/rewards/level_progress_card.dart';
import '../../widgets/rewards/streak_stats_row.dart';
import '../care/badge_detail_screen.dart';

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
                    IconButton(
                      onPressed: () => ShareService.instance.shareText(
                        "I'm on a ${provider.checkinStreak}-day check-in streak on MindCare — Level ${provider.levelNumber} · ${provider.levelName}!",
                        subject: 'My MindCare progress',
                      ),
                      icon: const Icon(Icons.ios_share, size: 18, color: AppColors.textDark),
                    ),
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
                  itemBuilder: (context, index) {
                    final badge = provider.badges[index];
                    return GestureDetector(
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => MobileFrame(child: BadgeDetailScreen(badge: badge))),
                      ),
                      child: BadgeTile(badge: badge),
                    );
                  },
                ),
                const SizedBox(height: 22),
                Text('EARN TODAY', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                ...List.generate(provider.earnTasks.length, (index) {
                  final task = provider.earnTasks[index];
                  return GestureDetector(
                    onTap: task.done
                        ? null
                        : () {
                            context.read<AccountProvider>().completeEarnTask(index);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('+${task.points} points · ${task.title} done!')),
                            );
                          },
                    child: EarnTodayTile(task: task),
                  );
                }),
              ],
            ),
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}