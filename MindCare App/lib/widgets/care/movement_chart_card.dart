import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

class MovementChartCard extends StatelessWidget {
  const MovementChartCard({
    super.key,
    required this.steps,
    required this.changePercent,
    required this.values,
    required this.dayLabels,
    required this.tip,
  });

  final int steps;
  final int changePercent;
  final List<double> values;
  final List<String> dayLabels;
  final String tip;

  String _formatSteps(int s) {
    final str = s.toString();
    if (str.length <= 3) return str;
    return '${str.substring(0, str.length - 3)},${str.substring(str.length - 3)}';
  }

  @override
  Widget build(BuildContext context) {
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
                        Text(_formatSteps(steps), style: AppTextStyles.heading(size: 24)),
                        const SizedBox(width: 6),
                        Text('steps · today', style: AppTextStyles.body(size: 12)),
                      ],
                    ),
                  ],
                ),
              ),
              Row(
                children: [
                  const Icon(Icons.arrow_upward, size: 13, color: AppColors.progressActive),
                  Text(' $changePercent%', style: const TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w600, fontSize: 13)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 18),
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
                          height: 60 * values[i],
                          decoration: BoxDecoration(
                            color: isLast ? AppColors.progressActive : AppColors.progressTrack,
                            borderRadius: BorderRadius.circular(6),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(dayLabels[i], style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                      ],
                    ),
                  ),
                );
              }),
            ),
          ),
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
      ),
    );
  }
}