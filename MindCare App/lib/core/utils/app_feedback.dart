import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// Consistent placeholder feedback for features that don't have a
/// full screen built yet. Ensures no button in the app is a silent
/// dead end — every tap gives the person visible confirmation, even
/// before the real destination screen exists.
void showComingSoon(BuildContext context, String feature) {
  ScaffoldMessenger.of(context).hideCurrentSnackBar();
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      behavior: SnackBarBehavior.floating,
      backgroundColor: AppColors.primaryDark,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      margin: const EdgeInsets.all(16),
      content: Text('$feature — coming soon', style: const TextStyle(color: Colors.white)),
    ),
  );
}