import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

/// Steps today (from the sensor) and recent daily steps (from the backend).
class MovementChartCard extends StatelessWidget {
  const MovementChartCard({
    super.key,
    required this.steps,
    required this.changePercent,
    required this.values,
    required this.dayLabels,
    required this.tip,
  });

  final int? steps;
  final int? changePercent;

  /// Daily step totals, oldest first.
  final List<int> values;
  final List<String> dayLabels;
  final String? tip;

  String _formatSteps(int s) {
    final str = s.toString();
    if (str.length <= 3) return str;
    return '${str.substring(0, str.length - 3)},${str.substring(str.length - 3)}';
  }

  @override
  Widget build(BuildContext context) {
    final maxSteps = values.isEmpty ? 0 : values.reduce((a, b) => a > b ? a : b);
    final change = changePercent;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.directions_walk, size: 16, color: AppColors.textDark),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('MOVEMENT', style: AppTextStyles.label()),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Text(steps == null ? '—' : _formatSteps(steps!), style: AppTextStyles.heading(size: 24)),
                        const SizedBox(width: 6),
                        Text('steps · today', style: AppTextStyles.body(size: 12)),
                      ],
                    ),
                  ],
                ),
              ),
              if (change != null)
                Row(
                  children: [
                    Icon(
                      change >= 0 ? Icons.arrow_upward : Icons.arrow_downward,
                      size: 13,
                      color: change >= 0 ? AppColors.progressActive : AppColors.sos,
                    ),
                    Text(
                      ' ${change.abs()}%',
                      style: TextStyle(color: change >= 0 ? AppColors.progressActive : AppColors.sos, fontWeight: FontWeight.w600, fontSize: 13),
                    ),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 18),
          if (values.isEmpty || maxSteps == 0)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 22),
              decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(14)),
              child: Text(
                'Your daily steps will show here once your sensor shares them.',
                textAlign: TextAlign.center,
                style: AppTextStyles.body(size: 13),
              ),
            )
          else
            SizedBox(
              height: 96,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: List.generate(values.length, (i) {
                  final isLast = i == values.length - 1;
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          Container(
                            height: 60 * values[i] / maxSteps,
                            decoration: BoxDecoration(
                              color: isLast ? AppColors.progressActive : AppColors.progressTrack,
                              borderRadius: BorderRadius.circular(6),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(i < dayLabels.length ? dayLabels[i] : '', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                        ],
                      ),
                    ),
                  );
                }),
              ),
            ),
          if (tip != null) ...[
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(14)),
              child: RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 13, color: AppColors.textDark, height: 1.4),
                  children: [
                    const TextSpan(text: 'Tip: ', style: TextStyle(fontWeight: FontWeight.w700)),
                    TextSpan(text: tip),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
