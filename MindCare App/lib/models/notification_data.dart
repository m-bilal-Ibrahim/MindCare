import 'package:flutter/material.dart';

class NotificationItem {
  const NotificationItem({
    required this.id,
    required this.icon,
    required this.iconBackground,
    required this.title,
    required this.subtitle,
    required this.timeAgo,
    required this.isToday,
    this.isRead = false,
  });

  final String id;
  final IconData icon;
  final Color iconBackground;
  final String title;
  final String subtitle;
  final String timeAgo;
  final bool isToday;
  final bool isRead;

  NotificationItem copyWith({bool? isRead}) {
    return NotificationItem(
      id: id,
      icon: icon,
      iconBackground: iconBackground,
      title: title,
      subtitle: subtitle,
      timeAgo: timeAgo,
      isToday: isToday,
      isRead: isRead ?? this.isRead,
    );
  }
}