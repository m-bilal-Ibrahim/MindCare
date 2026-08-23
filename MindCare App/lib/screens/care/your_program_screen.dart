import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/program_provider.dart';
import '../../widgets/care/program_task_tile.dart';
import '../../widgets/common/sos_button.dart';

class YourProgramScreen extends StatelessWidget {
  const YourProgramScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProgramProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 130),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'CARE PLAN',
                        textAlign: TextAlign.center,
                        style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                      ),
                    ),
                    IconButton(onPressed: () {}, icon: const Icon(Icons.more_horiz, color: AppColors.textDark)),
                  ],
                ),
                const SizedBox(height: 6),
                Text.rich(
                  TextSpan(
                    style: AppTextStyles.heading(size: 30),
                    children: [
                      const TextSpan(text: 'Your weekly\n'),
                      TextSpan(text: 'program.', style: AppTextStyles.heading(size: 30, style: FontStyle.italic)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                  child: Row(
                    children: [
                      const CircleAvatar(radius: 24, backgroundColor: AppColors.moodStressed, child: Text('TM', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700))),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Set by Dr. Tariq', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                            const SizedBox(height: 2),
                            Text('Updated 3 days ago · next review on Friday\'s session', style: AppTextStyles.body(size: 12)),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.shield_outlined, size: 12, color: AppColors.progressActive),
                            SizedBox(width: 4),
                            Text('permanent', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.progressActive)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('THIS WEEK', style: AppTextStyles.label()),
                    Text('${provider.totalDone} of ${provider.totalTasks} done', style: AppTextStyles.body(size: 13)),
                  ],
                ),
                const SizedBox(height: 12),
                ...provider.weeklyTasks.map((task) => ProgramTaskTile(task: task)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.lock_outline, size: 14, color: AppColors.textMuted),
                    const SizedBox(width: 8),
                    Expanded(
                      child: RichText(
                        text: TextSpan(
                          style: AppTextStyles.body(size: 12),
                          children: const [
                            TextSpan(text: 'Only Dr. Tariq can change your program. '),
                            TextSpan(text: 'Request a change →', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text('QUICK RELIEF FROM AIDA', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                Text('temporary · for right now', style: AppTextStyles.body(size: 12)),
              ],
            ),
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}