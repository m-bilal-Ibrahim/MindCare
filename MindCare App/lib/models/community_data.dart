import 'package:flutter/material.dart';

class CircleTag {
  const CircleTag({required this.name, required this.memberCount, required this.gradientColors});
  final String name;
  final String memberCount;
  final List<Color> gradientColors;
}

class CommunityPost {
  const CommunityPost({
    required this.id,
    required this.authorName,
    required this.handle,
    required this.avatarColor,
    required this.circleName,
    required this.timeAgo,
    required this.content,
    required this.hearts,
    required this.hugs,
    required this.comments,
    this.isAnonymous = false,
  });

  final String id;
  final String authorName;
  final String handle;
  final Color avatarColor;
  final String circleName;
  final String timeAgo;
  final String content;
  final int hearts;
  final int hugs;
  final int comments;
  final bool isAnonymous;
}

class SosResource {
  const SosResource({
    required this.icon,
    required this.iconBackground,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final Color iconBackground;
  final String title;
  final String subtitle;
}