import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/notifications_provider.dart';
import '../../widgets/notifications/notification_tile.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificationsProvider>();

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
                TextButton(
                  onPressed: provider.unreadCount == 0 ? null : () => context.read<NotificationsProvider>().markAllRead(),
                  child: Text(
                    'Mark all read',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: provider.unreadCount == 0 ? AppColors.textMuted : AppColors.progressActive,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (provider.todayItems.isNotEmpty) ...[
              const Padding(
                padding: EdgeInsets.only(bottom: 10, left: 4),
                child: Text('TODAY', style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 11)),
              ),
              ...provider.todayItems.map(
                (item) => NotificationTile(item: item, onTap: () => context.read<NotificationsProvider>().markRead(item.id)),
              ),
              const SizedBox(height: 14),
            ],
            if (provider.earlierItems.isNotEmpty) ...[
              const Padding(
                padding: EdgeInsets.only(bottom: 10, left: 4),
                child: Text('EARLIER', style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 11)),
              ),
              ...provider.earlierItems.map(
                (item) => NotificationTile(item: item, onTap: () => context.read<NotificationsProvider>().markRead(item.id)),
              ),
            ],
            if (provider.todayItems.isEmpty && provider.earlierItems.isEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 60),
                child: Column(
                  children: const [
                    Icon(Icons.notifications_none, size: 40, color: AppColors.textMuted),
                    SizedBox(height: 12),
                    Text("You're all caught up.", style: TextStyle(color: AppColors.textMuted)),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}