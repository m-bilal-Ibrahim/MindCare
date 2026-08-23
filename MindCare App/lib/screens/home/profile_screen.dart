import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/app_feedback.dart';
import '../../main.dart';
import '../../models/account_data.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/profile/profile_header.dart';
import '../../widgets/profile/profile_list_section.dart';
import 'rewards_screen.dart';
import 'wallet_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();

    final careItems = [
      ProfileListItem(icon: Icons.terrain, title: 'Your therapist', subtitle: '${provider.therapistName} · ${provider.therapistSince}'),
      ProfileListItem(icon: Icons.auto_awesome, title: 'Aida personality', trailing: provider.aidaPersonality),
      ProfileListItem(icon: Icons.bookmark_border, title: 'Past sessions & notes', trailing: '${provider.pastSessionsCount}', showDivider: false),
    ];

    final accountItems = [
      ProfileListItem(icon: Icons.watch_outlined, title: 'Wearables', subtitle: provider.wearableConnected ? 'MindBand · connected' : 'Not connected'),
      const ProfileListItem(icon: Icons.shield_outlined, title: 'Privacy & data', subtitle: 'What your therapist sees'),
      ProfileListItem(icon: Icons.notifications_none, title: 'Notifications', trailing: provider.notificationsOn ? 'On' : 'Off'),
      ProfileListItem(icon: Icons.credit_card, title: 'Billing & wallet', trailing: 'Rs ${provider.walletBalance}', showDivider: false),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 110),
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('YOU', style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12)),
                    IconButton(
                      onPressed: () => showComingSoon(context, 'Appearance settings'),
                      icon: const Icon(Icons.wb_sunny_outlined, color: AppColors.textDark, size: 20),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                GestureDetector(
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const MobileFrame(child: RewardsScreen())),
                  ),
                  child: ProfileHeader(
                    name: provider.userName,
                    joinedInfo: provider.joinedInfo,
                    levelBadge: 'Level ${provider.levelNumber} · Centered',
                    streak: provider.checkinStreak,
                    sessions: provider.statsSessions,
                    exercises: provider.statsExercises,
                  ),
                ),
                const SizedBox(height: 22),
                const Text('YOUR CARE', style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12)),
                const SizedBox(height: 12),
                ProfileListSection(
                  items: careItems,
                  onItemTap: (index) {
                    switch (index) {
                      case 0:
                        showComingSoon(context, 'Therapist profile');
                        break;
                      case 1:
                        showComingSoon(context, 'Aida personality settings');
                        break;
                      case 2:
                        showComingSoon(context, 'Past sessions & notes');
                        break;
                    }
                  },
                ),
                const SizedBox(height: 22),
                const Text('ACCOUNT', style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12)),
                const SizedBox(height: 12),
                ProfileListSection(
                  items: accountItems,
                  onItemTap: (index) {
                    switch (index) {
                      case 0:
                        showComingSoon(context, 'Wearables settings');
                        break;
                      case 1:
                        showComingSoon(context, 'Privacy & data settings');
                        break;
                      case 2:
                        showComingSoon(context, 'Notification settings');
                        break;
                      case 3:
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const MobileFrame(child: WalletScreen())),
                        );
                        break;
                    }
                  },
                ),
              ],
            ),
            const Positioned(right: 16, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}