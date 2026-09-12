import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'sparkline.dart';

class VitalMetricCard extends StatelessWidget {
  const VitalMetricCard({
    super.key,
    required this.label,
    required this.value,
    required this.unit,
    required this.trend,
    required this.color,
  });

  final String label;
  final String value;
  final String unit;
  final List<double> trend;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(value, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w600, color: AppColors.textDark)),
              const SizedBox(width: 6),
              Text(unit, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
            ],
          ),
          const SizedBox(height: 10),
          Sparkline(values: trend, color: color),
        ],
      ),
    );
  }
}