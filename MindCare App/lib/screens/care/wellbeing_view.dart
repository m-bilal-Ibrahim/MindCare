import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/checkin_provider.dart';
import '../../providers/program_provider.dart';
import '../../widgets/care/calm_time_ring_card.dart';
import '../../widgets/care/meals_card.dart';
import '../../widgets/care/movement_chart_card.dart';
import '../../widgets/care/small_step_tile.dart';
import '../../widgets/care/water_card.dart';

/// Embedded inside the Pulse tab (toggled via segmented control) —
/// not a standalone route — so the bottom nav stays visible and on
/// the Pulse tab, matching the design.
///
/// Steps and calm time come from sensor readings; meals, water, small
/// steps and movement history come from the backend. Each card shows an
/// empty state until its data exists.
class WellbeingView extends StatelessWidget {
  const WellbeingView({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProgramProvider>();
    final checkin = context.watch<CheckinProvider>();

    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 110),
      children: [
        Text('WELLBEING', style: AppTextStyles.label()),
        const SizedBox(height: 8),
        Text('The small things, kept up.', style: AppTextStyles.heading(size: 26)),
        const SizedBox(height: 18),
        MovementChartCard(
          steps: checkin.vitals?.steps,
          changePercent: provider.stepsChangePercent,
          values: provider.movementByDay,
          dayLabels: provider.movementDayLabels,
          tip: provider.movementTip,
        ),
        const SizedBox(height: 14),
        IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(child: MealsCard(mealsDone: provider.mealsDone, note: provider.mealNote)),
              const SizedBox(width: 12),
              Expanded(child: WaterCard(filled: provider.waterGlassesFilled, goal: provider.waterGlassesGoal)),
            ],
          ),
        ),
        const SizedBox(height: 14),
        CalmTimeRingCard(calmToday: checkin.calmToday),
        const SizedBox(height: 22),
        Text("TODAY'S SMALL STEPS", style: AppTextStyles.label()),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
          child: provider.smallSteps.isEmpty
              ? Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    children: [
                      const Icon(Icons.checklist_rtl, size: 20, color: AppColors.textMuted),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'No small steps yet. Your therapist adds them to your care plan.',
                          style: AppTextStyles.body(size: 13),
                        ),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: List.generate(provider.smallSteps.length, (i) {
                    return SmallStepTile(
                      step: provider.smallSteps[i],
                      showDivider: i != provider.smallSteps.length - 1,
                      onTap: () => context.read<ProgramProvider>().toggleSmallStep(i),
                    );
                  }),
                ),
        ),
      ],
    );
  }
}
