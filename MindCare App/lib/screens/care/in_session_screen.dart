import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/common/sos_button.dart';

class InSessionScreen extends StatefulWidget {
  const InSessionScreen({super.key});

  @override
  State<InSessionScreen> createState() => _InSessionScreenState();
}

class _InSessionScreenState extends State<InSessionScreen> {
  Timer? _timer;
  int _elapsedSeconds = 12 * 60 + 34;
  bool _micOn = true;
  bool _camOn = true;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsedSeconds++);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String get _formattedTime {
    final minutes = (_elapsedSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (_elapsedSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final therapist = context.watch<TherapyProvider>().selectedTherapist;
    final name = therapist?.name ?? 'Your therapist';

    return Scaffold(
      backgroundColor: const Color(0xFF241611),
      body: SafeArea(
        child: Container(
          decoration: const BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0, -0.2),
              radius: 1.2,
              colors: [Color(0xFF5A3A24), Color(0xFF241611)],
            ),
          ),
          child: Stack(
            children: [
              Positioned(
                top: 16,
                left: 16,
                right: 16,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(color: Colors.black.withOpacity(0.35), borderRadius: BorderRadius.circular(20)),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFFE5382B), shape: BoxShape.circle)),
                          const SizedBox(width: 6),
                          const Text('MEET · LIVE', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                          const SizedBox(width: 8),
                          Text(_formattedTime, style: const TextStyle(color: Colors.white70, fontSize: 11)),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(color: Colors.black.withOpacity(0.35), borderRadius: BorderRadius.circular(20)),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.auto_awesome, size: 13, color: Colors.white),
                          SizedBox(width: 6),
                          Text('Aida is taking notes', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                top: 76,
                right: 16,
                child: Container(
                  width: 108,
                  height: 148,
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFB4707A), Color(0xFF6E3A44)],
                    ),
                  ),
                  child: Stack(
                    children: [
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Icon(_micOn ? Icons.mic_none : Icons.mic_off, size: 14, color: Colors.white70),
                      ),
                      const Positioned(
                        left: 10,
                        bottom: 8,
                        child: Text('You', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                ),
              ),
              Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 130,
                      height: 130,
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.12), shape: BoxShape.circle),
                    ),
                    const SizedBox(height: 34),
                    Text(name, style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif')),
                    const SizedBox(height: 6),
                    const Text('Speaking...', style: TextStyle(color: Colors.white60, fontSize: 14)),
                  ],
                ),
              ),
              Positioned(
                left: 16,
                right: 16,
                bottom: 128,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                  decoration: BoxDecoration(color: Colors.black.withOpacity(0.4), borderRadius: BorderRadius.circular(16)),
                  child: const Text(
                    '"Let\'s stay with that thought a moment — what does it sound like in your head?"',
                    style: TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
                  ),
                ),
              ),
              Positioned(
                left: 16,
                right: 16,
                bottom: 24,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _ControlButton(icon: _micOn ? Icons.mic_none : Icons.mic_off, onTap: () => setState(() => _micOn = !_micOn)),
                    _ControlButton(icon: _camOn ? Icons.videocam_outlined : Icons.videocam_off_outlined, onTap: () => setState(() => _camOn = !_camOn)),
                    _ControlButton(icon: Icons.chat_bubble_outline, onTap: () {}),
                    _ControlButton(icon: Icons.more_horiz, onTap: () {}),
                    _EndCallButton(onTap: () => Navigator.of(context).maybePop()),
                  ],
                ),
              ),
              const Positioned(right: 16, bottom: 100, child: SosButton()),
            ],
          ),
        ),
      ),
    );
  }
}

class _ControlButton extends StatelessWidget {
  const _ControlButton({required this.icon, required this.onTap});
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), shape: BoxShape.circle),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
    );
  }
}

class _EndCallButton extends StatelessWidget {
  const _EndCallButton({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: const BoxDecoration(color: Color(0xFFD8664B), shape: BoxShape.circle),
        child: const Icon(Icons.call_end, color: Colors.white, size: 20),
      ),
    );
  }
}