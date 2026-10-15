import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/constants/emergency_numbers.dart';

/// SOS: a call button for the mental health helpline and a fixed list of
/// verified national emergency numbers. Contacts, nearby help and the SOS
/// log come later with the SOS backend.
class SosScreen extends StatelessWidget {
  const SosScreen({super.key});

  /// Opens the phone's own dialer, pre-filled with the number. MindCare never
  /// places the call itself: the person sees the number, confirms, and calls
  /// through their normal phone app.
  Future<void> _call(BuildContext context, EmergencyNumber number) async {
    final launched = await launchUrl(Uri(scheme: 'tel', path: number.dial));
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Couldn't open the dialer. Call ${number.display} directly.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final helpline = emergencyNumbers.first;

    return Scaffold(
      backgroundColor: const Color(0xFFF7DCD6),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.of(context).maybePop(),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: const Icon(Icons.close, size: 18, color: Color(0xFF3A2620)),
                  ),
                ),
                const Expanded(
                  child: Text(
                    'YOU ARE SAFE HERE',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: Color(0xFFB35440), fontWeight: FontWeight.w700, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 40),
              ],
            ),
            const SizedBox(height: 24),
            const Text.rich(
              TextSpan(
                style: TextStyle(color: Color(0xFFB0503C), fontSize: 30, fontFamily: 'serif', height: 1.25),
                children: [
                  TextSpan(text: "We're with you,\n"),
                  TextSpan(text: 'right now.', style: TextStyle(fontStyle: FontStyle.italic, color: Color(0xFFB0503C))),
                ],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 14),
            const Text(
              'Talk to someone now, or call emergency services if you or someone else is in danger.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFFC17A63), fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 34),
            Center(
              child: Semantics(
                button: true,
                label: 'Call ${helpline.name}, ${helpline.display}',
                child: GestureDetector(
                  onTap: () => _call(context, helpline),
                  child: Container(
                    width: 220,
                    height: 220,
                    decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFFF0C3B8).withValues(alpha: 0.5)),
                    child: Center(
                      child: Container(
                        width: 180,
                        height: 180,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: RadialGradient(colors: [Color(0xFFC96A50), Color(0xFFAD4C36)]),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text('Call a person', style: TextStyle(color: Colors.white, fontSize: 20, fontFamily: 'serif')),
                            const SizedBox(height: 6),
                            Text(helpline.display, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                            const SizedBox(height: 6),
                            const Text('TAP TO CALL', style: TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.w700)),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              'EMERGENCY NUMBERS',
              style: TextStyle(letterSpacing: 1, color: Color(0xFFB35440), fontWeight: FontWeight.w700, fontSize: 12),
            ),
            const SizedBox(height: 12),
            for (final number in emergencyNumbers) _NumberTile(number: number, onTap: () => _call(context, number)),
          ],
        ),
      ),
    );
  }
}

class _NumberTile extends StatelessWidget {
  const _NumberTile({required this.number, required this.onTap});
  final EmergencyNumber number;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(color: number.color, borderRadius: BorderRadius.circular(12)),
                  child: Icon(number.icon, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(number.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: Color(0xFF3A2620))),
                      const SizedBox(height: 2),
                      Text(number.display, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Color(0xFFB0503C))),
                      const SizedBox(height: 2),
                      Text(number.description, style: const TextStyle(fontSize: 12, color: Color(0xFF8A6D65))),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  width: 40,
                  height: 40,
                  decoration: const BoxDecoration(color: Color(0xFFF7DCD6), shape: BoxShape.circle),
                  child: const Icon(Icons.call, size: 18, color: Color(0xFFB0503C)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
