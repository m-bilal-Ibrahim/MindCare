import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/checkin_provider.dart';
import '../../widgets/pulse/calm_activated_strip.dart';
import '../../widgets/pulse/nervous_system_dial.dart';
import '../../widgets/pulse/vital_metric_card.dart';

class PulseScreen extends StatelessWidget {
  const PulseScreen({super.key});

  String _formatSteps(int steps) {
    final s = steps.toString();
    if (s.length <= 3) return s;
    return '${s.substring(0, s.length - 3)},${s.substring(s.length - 3)}';
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CheckinProvider>();
    final vitals = provider.vitals;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 110),
          children: [
            Text('PULSE', style: AppTextStyles.label()),
            const SizedBox(height: 8),
            Text('Your nervous system today', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 18),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 26),
              decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(24)),
              child: Column(
                children: [
                  Text('STATE RIGHT NOW', style: AppTextStyles.label()),
                  const SizedBox(height: 18),
                  const NervousSystemDial(state: 'Calm', subtitle: 'parasympathetic'),
                  const SizedBox(height: 18),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Text(
                      'Your body is settled. Stay with it — sip water, soften your shoulders.',
                      textAlign: TextAlign.center,
                      style: AppTextStyles.body(size: 14),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: VitalMetricCard(
                    label: 'HEART RATE',
                    value: '${vitals.heartRate}',
                    unit: 'bpm',
                    trend: vitals.heartTrend,
                    color: AppColors.moodStressed,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: VitalMetricCard(
                    label: 'BREATHING',
                    value: '${vitals.breathingRate}',
                    unit: '/min',
                    trend: vitals.breathingTrend,
                    color: AppColors.moodLow,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: VitalMetricCard(
                    label: 'SWEAT (EDA)',
                    value: vitals.sweatEda.toStringAsFixed(1),
                    unit: 'μS',
                    trend: vitals.sweatTrend,
                    color: AppColors.amberSegment,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: VitalMetricCard(
                    label: 'STEPS',
                    value: _formatSteps(vitals.steps),
                    unit: 'today',
                    trend: vitals.stepsTrend,
                    color: AppColors.progressActive,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 22),
            Text('CALM VS. ACTIVATED · TODAY', style: AppTextStyles.label()),
            const SizedBox(height: 12),
            CalmActivatedStrip(segments: provider.calmActivated),
          ],
        ),
      ),
    );
  }
}