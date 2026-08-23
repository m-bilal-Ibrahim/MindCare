import 'package:flutter/material.dart';

class Therapist {
  const Therapist({
    required this.id,
    required this.name,
    required this.initials,
    required this.avatarColor,
    required this.title,
    required this.specialty,
    required this.rating,
    required this.reviewCount,
    required this.yearsExperience,
    required this.languages,
    required this.priceMonthly,
    required this.priceYearly,
    required this.trialAvailable,
    required this.status,
    required this.credentialBadge,
  });

  final String id;
  final String name;
  final String initials;
  final Color avatarColor;
  final String title;
  final String specialty;
  final double rating;
  final int reviewCount;
  final int yearsExperience;
  final String languages;
  final int priceMonthly;
  final int priceYearly;
  final bool trialAvailable;
  final String status;
  final String credentialBadge;
}

class ScheduleSlot {
  const ScheduleSlot(this.time, this.status);
  final String time;
  final String status; // 'free', 'booked', 'off'
}

class WeekDay {
  const WeekDay(this.label, this.date);
  final String label;
  final int date;
}