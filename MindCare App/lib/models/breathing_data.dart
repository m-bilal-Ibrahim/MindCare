class BreathingPattern {
  const BreathingPattern({
    required this.title,
    required this.subtitle,
    required this.totalSeconds,
    required this.inhale,
    required this.hold1,
    required this.exhale,
    required this.hold2,
  });

  final String title;
  final String subtitle;
  final int totalSeconds;
  final int inhale;
  final int hold1;
  final int exhale;
  final int hold2;

  int get cycleSeconds => inhale + hold1 + exhale + hold2;

  static const boxBreathing = BreathingPattern(
    title: 'Box breathing',
    subtitle: '4 in · 4 hold · 4 out · 4 hold',
    totalSeconds: 90,
    inhale: 4,
    hold1: 4,
    exhale: 4,
    hold2: 4,
  );

  static const quickBreath = BreathingPattern(
    title: '3-min breath',
    subtitle: '4 in · 4 hold · 6 out · 2 hold',
    totalSeconds: 180,
    inhale: 4,
    hold1: 4,
    exhale: 6,
    hold2: 2,
  );
}