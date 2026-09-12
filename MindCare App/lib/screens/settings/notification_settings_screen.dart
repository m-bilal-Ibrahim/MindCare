import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/settings_provider.dart';

class NotificationSettingsScreen extends StatelessWidget {
  const NotificationSettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SettingsProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 30),
          children: [
            Row(
              children: [
                IconButton(
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                ),
                const Expanded(
                  child: Text(
                    'NOTIFICATIONS',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('Stay in the loop.', style: AppTextStyles.heading(size: 28)),
            const SizedBox(height: 8),
            Text('Choose what MindCare can notify you about.', style: AppTextStyles.body()),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
              child: Row(
                children: [
                  const Expanded(
                    child: Text('All notifications', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                  ),
                  Switch(
                    value: provider.allNotificationsOn,
                    activeThumbColor: AppColors.primaryDark,
                    onChanged: (value) => context.read<SettingsProvider>().setAllNotifications(value),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            Text('BY CATEGORY', style: AppTextStyles.label()),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
              child: Column(
                children: List.generate(provider.notificationCategories.length, (i) {
                  final category = provider.notificationCategories[i];
                  return Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(category.title, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark, fontSize: 14)),
                                  const SizedBox(height: 3),
                                  Text(category.subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                ],
                              ),
                            ),
                            Switch(
                              value: category.enabled,
                              activeThumbColor: AppColors.primaryDark,
                              onChanged: (_) => context.read<SettingsProvider>().toggleNotificationCategory(category.id),
                            ),
                          ],
                        ),
                      ),
                      if (i != provider.notificationCategories.length - 1) const Divider(height: 1, indent: 16, endIndent: 16, color: AppColors.border),
                    ],
                  );
                }),
              ),
            ),
          ],
        ),
      ),
    );
  }
}