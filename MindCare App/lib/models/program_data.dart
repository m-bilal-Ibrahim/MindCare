import 'package:flutter/material.dart';

class WeeklyTask {
  const WeeklyTask({
    required this.category,
    required this.schedule,
    required this.title,
    required this.done,
    required this.total,
    required this.color,
  });

  final String category;
  final String schedule;
  final String title;
  final int done;
  final int total;
  final Color color;
}

class DailyStep {
  const DailyStep(this.label, this.done);
  final String label;
  final bool done;
}

class AudioTrack {
  const AudioTrack({
    required this.id,
    required this.tag,
    required this.title,
    this.arabic,
    required this.translation,
    required this.duration,
  });

  final String id;
  final String tag;
  final String title;
  final String? arabic;
  final String translation;
  final String duration;
}