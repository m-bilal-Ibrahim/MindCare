import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/therapy_data.dart';

class TherapistCard extends StatelessWidget {
  const TherapistCard({super.key, required this.therapist, required this.onViewPlan});
  final Therapist therapist;
  final VoidCallback onViewPlan;

  String _formatPrice(int price) {
    final s = price.toString();
    final buffer = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i != 0 && (s.length - i) % 3 == 0) buffer.write(',');
      buffer.write(s[i]);
    }
    return buffer.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 26,
                backgroundColor: therapist.avatarColor,
                child: Text(therapist.initials, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(therapist.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: AppColors.textDark)),
                    const SizedBox(height: 2),
                    Text(therapist.specialty, style: const TextStyle(fontSize: 13, color: AppColors.textMuted)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.star, size: 13, color: Color(0xFFC79A56)),
                        const SizedBox(width: 3),
                        Text('${therapist.rating} (${therapist.reviewCount})', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                        Text('  ·  ${therapist.yearsExperience} yrs  ·  ${therapist.languages}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('Rs ${_formatPrice(therapist.priceMonthly)}', style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                  const Text('/ month', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              if (therapist.trialAvailable) _Tag(label: '7-day trial', bg: const Color(0xFFF0DEB9)),
              if (therapist.trialAvailable) const SizedBox(width: 8),
              _Tag(
                label: therapist.status,
                bg: therapist.status == 'Open' ? const Color(0xFFDCEAE2) : const Color(0xFFF0DBD3),
                dot: true,
                dotColor: therapist.status == 'Open' ? AppColors.progressActive : AppColors.sos,
              ),
              const Spacer(),
              ElevatedButton(
                onPressed: onViewPlan,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.progressActive,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                ),
                child: const Text('View plan', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.label, required this.bg, this.dot = false, this.dotColor});
  final String label;
  final Color bg;
  final bool dot;
  final Color? dotColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (dot) ...[
            Container(width: 6, height: 6, decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle)),
            const SizedBox(width: 5),
          ],
          Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.textDark)),
        ],
      ),
    );
  }
}