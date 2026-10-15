import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../common/skeleton.dart';

/// Arabic text style for duas and surahs.
TextStyle arabicStyle({double size = 24, Color color = Colors.white}) =>
    GoogleFonts.amiri(fontSize: size, color: color, height: 1.9);

/// What the content being loaded looks like, so the skeleton matches it.
enum MotivationSkeletonKind { quote, quoteCards, rows, verses }

/// Skeleton placeholder for Motivation content. After a few seconds it also
/// explains the server may be waking up (the first request can take ~40–50 s).
class MotivationSkeleton extends StatefulWidget {
  const MotivationSkeleton({super.key, required this.kind, this.count = 3, this.showWakeNote = true});

  final MotivationSkeletonKind kind;
  final int count;
  final bool showWakeNote;

  @override
  State<MotivationSkeleton> createState() => _MotivationSkeletonState();
}

class _MotivationSkeletonState extends State<MotivationSkeleton> {
  Timer? _timer;
  bool _slow = false;

  @override
  void initState() {
    super.initState();
    if (widget.showWakeNote) {
      _timer = Timer(const Duration(seconds: 6), () {
        if (mounted) setState(() => _slow = true);
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Widget _card(Widget child) => Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(18)),
        child: child,
      );

  Widget _shape() {
    switch (widget.kind) {
      case MotivationSkeletonKind.quote:
        return const Padding(
          padding: EdgeInsets.symmetric(horizontal: 12),
          child: Column(
            children: [
              SkeletonLines(lines: 3, lineHeight: 18, gap: 12, lastWidthFactor: 0.55, center: true),
              SizedBox(height: 16),
              SkeletonBox(width: 110, height: 11, radius: 6),
            ],
          ),
        );
      case MotivationSkeletonKind.quoteCards:
        return Column(
          children: [
            for (var i = 0; i < widget.count; i++)
              _card(const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SkeletonLines(lines: 2, lineHeight: 13, lastWidthFactor: 0.7),
                  SizedBox(height: 14),
                  Row(children: [SkeletonBox(width: 90, height: 10), Spacer(), SkeletonBox(width: 64, height: 18, radius: 9)]),
                ],
              )),
          ],
        );
      case MotivationSkeletonKind.rows:
        return Column(
          children: [
            for (var i = 0; i < widget.count; i++)
              _card(const Row(
                children: [
                  SkeletonBox(height: 40, circle: true),
                  SizedBox(width: 14),
                  Expanded(child: SkeletonLines(lines: 2, lineHeight: 12, lastWidthFactor: 0.5)),
                  SizedBox(width: 12),
                  SkeletonBox(width: 44, height: 16),
                ],
              )),
          ],
        );
      case MotivationSkeletonKind.verses:
        return Column(
          children: [
            for (var i = 0; i < widget.count; i++)
              _card(const Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      SkeletonBox(height: 26, circle: true),
                      SizedBox(width: 10),
                      Expanded(child: SkeletonLines(lines: 1, lineHeight: 20, alignEnd: true)),
                    ],
                  ),
                  SizedBox(height: 12),
                  SkeletonLines(lines: 2, lineHeight: 12, lastWidthFactor: 0.65),
                ],
              )),
          ],
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Shimmer(base: Shimmer.darkBase, highlight: Shimmer.darkHighlight, child: _shape()),
        if (_slow)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text(
              'MindCare is waking up. This can take up to a minute the first time.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white60, fontSize: 12, height: 1.4),
            ),
          ),
      ],
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
