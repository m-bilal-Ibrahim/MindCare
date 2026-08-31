import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/breathing_data.dart';
import '../../widgets/care/breathing_circle_animation.dart';
import '../../widgets/common/primary_button.dart';

class BreathingPlayerScreen extends StatefulWidget {
  const BreathingPlayerScreen({super.key, required this.pattern});
  final BreathingPattern pattern;

  @override
  State<BreathingPlayerScreen> createState() => _BreathingPlayerScreenState();
}

class _BreathingPlayerScreenState extends State<BreathingPlayerScreen> {
  late int _remainingSeconds;
  Timer? _timer;
  bool _isPaused = false;
  bool _isComplete = false;
  String _phaseLabel = 'Breathe in';

  @override
  void initState() {
    super.initState();
    _remainingSeconds = widget.pattern.totalSeconds;
    _startTimer();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_isPaused) return;
      setState(() {
        if (_remainingSeconds <= 1) {
          _remainingSeconds = 0;
          _isComplete = true;
          _timer?.cancel();
        } else {
          _remainingSeconds--;
        }
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String get _formattedTime {
    final m = (_remainingSeconds ~/ 60).toString().padLeft(2, '0');
    final s = (_remainingSeconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF16241F),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: _isComplete ? _buildComplete(context) : _buildActive(),
        ),
      ),
    );
  }

  Widget _buildActive() {
    return Column(
      children: [
        Row(
          children: [
            IconButton(
              onPressed: () => Navigator.of(context).maybePop(),
              icon: const Icon(Icons.close, color: Colors.white70),
            ),
            Expanded(
              child: Text(
                widget.pattern.title,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, letterSpacing: 1, fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(width: 48),
          ],
        ),
        const Spacer(),
        BreathingCircleAnimation(
          pattern: widget.pattern,
          isPaused: _isPaused,
          onPhaseChanged: (phase) => setState(() => _phaseLabel = phase),
        ),
        const SizedBox(height: 40),
        Text(_phaseLabel, style: const TextStyle(color: Colors.white, fontSize: 24, fontFamily: 'serif')),
        const SizedBox(height: 12),
        Text(widget.pattern.subtitle, style: const TextStyle(color: Colors.white54, fontSize: 13)),
        const Spacer(),
        Text(_formattedTime, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
        const SizedBox(height: 24),
        GestureDetector(
          onTap: () => setState(() => _isPaused = !_isPaused),
          child: Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.12), shape: BoxShape.circle),
            child: Icon(_isPaused ? Icons.play_arrow : Icons.pause, color: Colors.white, size: 28),
          ),
        ),
        const SizedBox(height: 40),
      ],
    );
  }

  Widget _buildComplete(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 90,
          height: 90,
          decoration: const BoxDecoration(color: Color(0xFF5C8B78), shape: BoxShape.circle),
          child: const Icon(Icons.check, color: Colors.white, size: 40),
        ),
        const SizedBox(height: 28),
        const Text('Well done.', style: TextStyle(color: Colors.white, fontSize: 28, fontFamily: 'serif')),
        const SizedBox(height: 10),
        Text(
          'You just spent ${widget.pattern.totalSeconds ~/ 60} minutes settling your body.',
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.white60, fontSize: 14),
        ),
        const SizedBox(height: 40),
        PrimaryButton(label: 'Done', icon: null, onPressed: () => Navigator.of(context).maybePop()),
      ],
    );
  }
}