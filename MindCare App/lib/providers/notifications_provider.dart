import 'package:flutter/material.dart';
import '../models/notification_data.dart';

class NotificationsProvider extends ChangeNotifier {
  List<NotificationItem> _items = [
    NotificationItem(
      id: 'n1',
      icon: Icons.terrain,
      iconBackground: const Color(0xFFDCEAE2),
      title: 'Dr. Tariq confirmed your session',
      subtitle: 'Friday · 5:00 PM. See it on your schedule.',
      timeAgo: '1h',
      isToday: true,
    ),
    NotificationItem(
      id: 'n2',
      icon: Icons.auto_awesome,
      iconBackground: const Color(0xFFDDE3F0),
      title: 'Aida noticed your heart rate settle',
      subtitle: 'Nice work with the box breath earlier.',
      timeAgo: '3h',
      isToday: true,
    ),
    NotificationItem(
      id: 'n3',
      icon: Icons.local_fire_department,
      iconBackground: const Color(0xFFF0DEB9),
      title: '14-day check-in streak!',
      subtitle: "You've shown up two weeks straight.",
      timeAgo: 'Yesterday',
      isToday: false,
      isRead: true,
    ),
    NotificationItem(
      id: 'n4',
      icon: Icons.groups,
      iconBackground: const Color(0xFFDCEAE2),
      title: 'New reply in Sober walk',
      subtitle: 'Someone replied to a post you hearted.',
      timeAgo: '2d',
      isToday: false,
      isRead: true,
    ),
  ];

  List<NotificationItem> get todayItems => _items.where((n) => n.isToday).toList();
  List<NotificationItem> get earlierItems => _items.where((n) => !n.isToday).toList();
  int get unreadCount => _items.where((n) => !n.isRead).length;

  void markAllRead() {
    _items = _items.map((n) => n.copyWith(isRead: true)).toList();
    notifyListeners();
  }

  void markRead(String id) {
    final index = _items.indexWhere((n) => n.id == id);
    if (index == -1 || _items[index].isRead) return;
    final updated = List<NotificationItem>.from(_items);
    updated[index] = updated[index].copyWith(isRead: true);
    _items = updated;
    notifyListeners();
  }
}