import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class CirclesPlaceholderScreen extends StatelessWidget {
  const CirclesPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.groups_outlined, size: 40, color: AppColors.textMuted),
                const SizedBox(height: 16),
                Text('Circles', style: AppTextStyles.heading(size: 22)),
                const SizedBox(height: 8),
                Text('Community spaces are coming soon.', textAlign: TextAlign.center, style: AppTextStyles.body()),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
