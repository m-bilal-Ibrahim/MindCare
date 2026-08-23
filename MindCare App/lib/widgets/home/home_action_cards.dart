import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class AidaListeningCard extends StatelessWidget {
  const AidaListeningCard({super.key, this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(20)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: const BoxDecoration(color: AppColors.primaryDark, shape: BoxShape.circle),
              child: const Icon(Icons.auto_awesome, color: Colors.white, size: 16),
            ),
            const SizedBox(height: 36),
            Text.rich(
              TextSpan(
                style: AppTextStyles.heading(size: 22),
                children: [
                  const TextSpan(text: 'Aida is\n'),
                  TextSpan(text: 'listening', style: AppTextStyles.heading(size: 22, style: FontStyle.italic)),
                ],
              ),
            ),
            const SizedBox(height: 4),
            Text('your guide', style: AppTextStyles.body(size: 13)),
          ],
        ),
      ),
    );
  }
}

class AppointmentCard extends StatelessWidget {
  const AppointmentCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.calendar_today_outlined, size: 18, color: AppColors.textDark),
          const SizedBox(height: 10),
          Text('IN 2 DAYS', style: AppTextStyles.label()),
          const SizedBox(height: 4),
          const Text('Fri · 5:00 PM', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
          Text('Dr. Tariq · Meet', style: AppTextStyles.body(size: 12)),
        ],
      ),
    );
  }
}

class QuickBreathCard extends StatelessWidget {
  const QuickBreathCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.eco_outlined, size: 18, color: AppColors.textDark),
          const SizedBox(height: 10),
          Text('QUICK', style: AppTextStyles.label()),
          const SizedBox(height: 4),
          const Text('3-min breath', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
        ],
      ),
    );
  }
}

class ActionPillRow extends StatelessWidget {
  const ActionPillRow({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _GradientPill(
            label: 'BREATH',
            colors: const [AppColors.breathGradientStart, AppColors.breathGradientEnd],
            onTap: () {},
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _GradientPill(
            label: 'REFLECT',
            colors: const [AppColors.reflectGradientStart, AppColors.reflectGradientEnd],
            onTap: () {},
          ),
        ),
      ],
    );
  }
}

class _GradientPill extends StatelessWidget {
  const _GradientPill({required this.label, required this.colors, required this.onTap});
  final String label;
  final List<Color> colors;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 64,
        padding: const EdgeInsets.symmetric(horizontal: 18),
        alignment: Alignment.centerLeft,
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: colors, begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
      ),
    );
  }
}