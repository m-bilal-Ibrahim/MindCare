import 'package:flutter/material.dart';
import '../../models/breathing_data.dart';

class BreathingCircleAnimation extends StatefulWidget {
  const BreathingCircleAnimation({
    super.key,
    required this.pattern,
    required this.isPaused,
    required this.onPhaseChanged,
  });

  final BreathingPattern pattern;
  final bool isPaused;
  final ValueChanged<String> onPhaseChanged;

  @override
  State<BreathingCircleAnimation> createState() => _BreathingCircleAnimationState();
}

class _BreathingCircleAnimationState extends State<BreathingCircleAnimation> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  double _scale = 0.6;
  String _lastPhase = '';

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: Duration(seconds: widget.pattern.cycleSeconds),
    )..addListener(_handleTick);
    if (!widget.isPaused) _controller.repeat();
  }

  void _handleTick() {
    final p = widget.pattern;
    final elapsed = _controller.value * p.cycleSeconds;
    String phase;
    double scale;

    if (elapsed < p.inhale) {
      phase = 'Breathe in';
      scale = 0.6 + 0.4 * (elapsed / p.inhale);
    } else if (elapsed < p.inhale + p.hold1) {
      phase = 'Hold';
      scale = 1.0;
    } else if (elapsed < p.inhale + p.hold1 + p.exhale) {
      phase = 'Breathe out';
      final t = (elapsed - p.inhale - p.hold1) / p.exhale;
      scale = 1.0 - 0.4 * t;
    } else {
      phase = 'Hold';
      scale = 0.6;
    }

    if (phase != _lastPhase) {
      _lastPhase = phase;
      widget.onPhaseChanged(phase);
    }
    setState(() => _scale = scale);
  }

  @override
  void didUpdateWidget(covariant BreathingCircleAnimation oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isPaused && _controller.isAnimating) {
      _controller.stop();
    } else if (!widget.isPaused && !_controller.isAnimating) {
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Transform.scale(
      scale: _scale,
      child: Container(
        width: 220,
        height: 220,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(colors: [Color(0xFF5C8B78), Color(0xFF1D3831)]),
          boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 30, spreadRadius: 2)],
        ),
      ),
    );
  }
}