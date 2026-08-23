import 'package:flutter/material.dart';

enum MessageSender { user, assistant }

enum NervousSystemState { calm, activated }

class DailyMoodOption {
  const DailyMoodOption(this.id, this.label, this.color);
  final String id;
  final String label;
  final Color color;
}

class VitalsSnapshot {
  const VitalsSnapshot({
    required this.heartRate,
    required this.breathingRate,
    required this.steps,
    required this.sweatEda,
    required this.heartTrend,
    required this.breathingTrend,
    required this.stepsTrend,
    required this.sweatTrend,
    required this.state,
  });

  final int heartRate;
  final int breathingRate;
  final int steps;
  final double sweatEda;
  final List<double> heartTrend;
  final List<double> breathingTrend;
  final List<double> stepsTrend;
  final List<double> sweatTrend;
  final String state;
}

class BreathingExercise {
  const BreathingExercise({
    required this.title,
    required this.subtitle,
    required this.ctaLabel,
  });

  final String title;
  final String subtitle;
  final String ctaLabel;
}

class ChatMessage {
  ChatMessage({
    required this.id,
    required this.sender,
    this.text,
    this.exercise,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  final String id;
  final MessageSender sender;
  final String? text;
  final BreathingExercise? exercise;
  final DateTime timestamp;
}

class ProgressInsight {
  const ProgressInsight({
    required this.icon,
    required this.iconBackground,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final Color iconBackground;
  final String title;
  final String description;
}