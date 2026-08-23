import 'package:flutter/material.dart';

class RewardBadge {
  const RewardBadge({required this.icon, required this.iconColor, required this.name, required this.unlocked});
  final IconData icon;
  final Color iconColor;
  final String name;
  final bool unlocked;
}

class EarnTask {
  const EarnTask({required this.title, required this.subtitle, required this.points, required this.done});
  final String title;
  final String subtitle;
  final int points;
  final bool done;
}

class PaymentMethod {
  const PaymentMethod({
    required this.id,
    required this.name,
    required this.lastFour,
    required this.expiry,
    required this.isDefault,
    required this.gradientColors,
  });

  final String id;
  final String name;
  final String lastFour;
  final String expiry;
  final bool isDefault;
  final List<Color> gradientColors;
}

class WalletTransaction {
  const WalletTransaction({
    required this.icon,
    required this.iconBackground,
    required this.title,
    required this.subtitle,
    required this.amount,
    required this.isCredit,
  });

  final IconData icon;
  final Color iconBackground;
  final String title;
  final String subtitle;
  final String amount;
  final bool isCredit;
}

class ProfileListItem {
  const ProfileListItem({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.showDivider = true,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final String? trailing;
  final bool showDivider;
}