import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Arabic text style for duas and surahs.
TextStyle arabicStyle({double size = 24, Color color = Colors.white}) =>
    GoogleFonts.amiri(fontSize: size, color: color, height: 1.9);

/// Spinner that, after a few seconds, explains the server may be waking up
/// (the backend can take ~40–50 s on the first request).
class MotivationLoading extends StatefulWidget {
  const MotivationLoading({super.key, this.label = 'Loading…'});
  final String label;

  @override
  State<MotivationLoading> createState() => _MotivationLoadingState();
}

class _MotivationLoadingState extends State<MotivationLoading> {
  Timer? _timer;
  bool _slow = false;

  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(seconds: 6), () {
      if (mounted) setState(() => _slow = true);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 30, horizontal: 24),
      child: Column(
        children: [
          const SizedBox(width: 26, height: 26, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white70)),
          const SizedBox(height: 14),
          Text(
            _slow ? 'MindCare is waking up. This can take up to a minute the first time.' : widget.label,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
          ),
        ],
      ),
    );
  }
}

/// A message with an optional action, for errors and empty lists.
class MotivationMessage extends StatelessWidget {
  const MotivationMessage({
    super.key,
    required this.icon,
    required this.title,
    this.body,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String? body;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 26, horizontal: 22),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(22)),
      child: Column(
        children: [
          Icon(icon, color: Colors.white70, size: 28),
          const SizedBox(height: 10),
          Text(title, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          if (body != null) ...[
            const SizedBox(height: 6),
            Text(body!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4)),
          ],
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 14),
            OutlinedButton(
              onPressed: onAction,
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Colors.white38),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: Text(actionLabel!),
            ),
          ],
        ],
      ),
    );
  }
}

/// Error from the backend, or "please sign in again" when the session ended.
class MotivationError extends StatelessWidget {
  const MotivationError({super.key, required this.message, required this.sessionExpired, required this.onRetry});
  final String message;
  final bool sessionExpired;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return MotivationMessage(
      icon: sessionExpired ? Icons.lock_outline : Icons.cloud_off_outlined,
      title: sessionExpired ? 'Please sign in again' : "Couldn't load this",
      body: message,
      actionLabel: sessionExpired ? 'Sign in' : 'Try again',
      onAction: sessionExpired ? () => Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (_) => false) : onRetry,
    );
  }
}

/// Source credit the backend asks the App to show for Quran text.
const String quranAttribution =
    'Arabic text: Tanzil Quran Text (Simple), CC BY 3.0, tanzil.net. English translation: Pickthall (1930).';
