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

/// One day in the booking strip.
class WeekDay {
  const WeekDay(this.day);
  final DateTime day;

  static const _labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  String get label => _labels[day.weekday - 1];
  int get date => day.day;
}

/// A session time the patient asked for, waiting for the psychologist.
class SessionRequest {
  const SessionRequest({required this.day, required this.time, required this.requestedAt, this.isReschedule = false});
  final DateTime day;
  final String time; // e.g. "5:00 PM"
  final DateTime requestedAt;
  final bool isReschedule;
}

/// The patient's next booked session, as supplied by the backend.
class UpcomingSession {
  const UpcomingSession({required this.startsAt, required this.therapistName, required this.mode});
  final DateTime startsAt;
  final String therapistName;
  final String mode; // e.g. 'Meet', 'In person'
}
