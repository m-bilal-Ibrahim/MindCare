import 'package:flutter/material.dart';

class RewardBadge {
  const RewardBadge({
    required this.icon,
    required this.iconColor,
    required this.name,
    required this.unlocked,
    required this.description,
    required this.criteria,
    this.unlockedDate,
  });

  final IconData icon;
  final Color iconColor;
  final String name;
  final bool unlocked;
  final String description;
  final String criteria;
  final String? unlockedDate;
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

class CircleContact {
  const CircleContact({required this.name, required this.relation, required this.avatarColor, this.notified = false});
  final String name;
  final String relation;
  final Color avatarColor;
  final bool notified;

  CircleContact copyWith({bool? notified}) {
    return CircleContact(name: name, relation: relation, avatarColor: avatarColor, notified: notified ?? this.notified);
  }
}

class AidaPersonalityOption {
  const AidaPersonalityOption({
    required this.name,
    required this.tagline,
    required this.description,
    required this.icon,
    required this.color,
  });

  final String name;
  final String tagline;
  final String description;
  final IconData icon;
  final Color color;
}

class PastSession {
  const PastSession({
    required this.therapistName,
    required this.date,
    required this.durationMinutes,
    required this.summary,
    this.hasSharedNotes = false,
  });

  final String therapistName;
  final String date;
  final int durationMinutes;
  final String summary;
  final bool hasSharedNotes;
}

class TherapistProfile {
  const TherapistProfile({
    required this.name,
    required this.credentials,
    required this.since,
    required this.bio,
    required this.specialties,
    required this.languages,
    required this.rating,
    required this.sessionsWithYou,
  });

  final String name;
  final String credentials;
  final String since;
  final String bio;
  final List<String> specialties;
  final List<String> languages;
  final double rating;
  final int sessionsWithYou;
}