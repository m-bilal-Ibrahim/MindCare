import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/notification_data.dart';

class NotificationTile extends StatelessWidget {
  const NotificationTile({super.key, required this.item, this.onTap});
  final NotificationItem item;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: item.isRead ? Colors.white : AppColors.infoBoxBackground,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: item.iconBackground, borderRadius: BorderRadius.circular(12)),
              child: Icon(item.icon, size: 18, color: AppColors.textDark),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textDark)),
                  const SizedBox(height: 3),
                  Text(item.subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted, height: 1.35)),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(item.timeAgo, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                if (!item.isRead) ...[
                  const SizedBox(height: 6),
                  Container(width: 7, height: 7, decoration: const BoxDecoration(color: AppColors.sos, shape: BoxShape.circle)),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}