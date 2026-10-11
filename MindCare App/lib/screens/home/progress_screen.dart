import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/share_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/checkin_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/progress/insight_tile.dart';
import '../../widgets/progress/mood_timeline_chart.dart';
import '../../widgets/progress/streak_summary_row.dart';

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CheckinProvider>();
    final hasData = provider.streakDays > 0 || provider.avgMood != null || provider.moodTimeline.isNotEmpty;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 110),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'Your progress',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark),
                      ),
                    ),
                    if (hasData)
                      IconButton(
                        onPressed: () => ShareService.instance.shareText(
                          "${provider.streakDays}-day check-in streak on MindCare"
                          "${provider.avgMood == null ? '' : ', average mood ${provider.avgMood!.toStringAsFixed(1)}/5 this month'}.",
                          subject: 'My MindCare progress',
                        ),
                        icon: const Icon(Icons.ios_share, color: AppColors.textDark, size: 20),
                      )
                    else
                      const SizedBox(width: 48),
                  ],
                ),
                const SizedBox(height: 12),
                Text(hasData ? "You've been showing up." : 'Your progress starts here.', style: AppTextStyles.heading(size: 30)),
                const SizedBox(height: 6),
                Text(
                  hasData ? 'Last 30 days, gently summarized.' : 'Check in each day and this page fills in with your own patterns.',
                  style: AppTextStyles.body(),
                ),
                const SizedBox(height: 20),
                StreakSummaryRow(
                  streakDays: provider.streakDays,
                  avgMood: provider.avgMood,
                  avgMoodDelta: provider.avgMoodDelta,
                ),
                const SizedBox(height: 22),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('MOOD TIMELINE', style: AppTextStyles.label()),
                    Container(
                      padding: const EdgeInsets.all(3),
                      decoration: BoxDecoration(color: AppColors.progressTrack.withValues(alpha: 0.5), borderRadius: BorderRadius.circular(14)),
                      child: TimelineRangeSelector(
                        selected: provider.moodRange,
                        onChanged: (range) => context.read<CheckinProvider>().setMoodRange(range),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                MoodTimelineChart(values: provider.moodTimeline, labels: provider.moodTimelineLabels),
                const SizedBox(height: 22),
                Text('WHAT WE SEE', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                if (provider.insights.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(18)),
                    child: Row(
                      children: [
                        const Icon(Icons.lightbulb_outline, size: 20, color: AppColors.textMuted),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Patterns from your check-ins and sensor data will appear here once there is enough to learn from.',
                            style: AppTextStyles.body(size: 13),
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  ...provider.insights.map((insight) => InsightTile(insight: insight)),
              ],
            ),
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}