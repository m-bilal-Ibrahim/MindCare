import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/share_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/program_provider.dart';
import '../../widgets/care/program_task_tile.dart';
import '../../widgets/common/sos_button.dart';
import 'past_programs_screen.dart';
import 'request_change_screen.dart';

class YourProgramScreen extends StatelessWidget {
  const YourProgramScreen({super.key});

  void _showMoreOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: const Icon(Icons.edit_note_outlined, color: AppColors.textDark),
                  title: const Text('Request a change', style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark)),
                  onTap: () {
                    Navigator.of(sheetContext).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const MobileFrame(child: RequestChangeScreen())),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.history, color: AppColors.textDark),
                  title: const Text('View past programs', style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark)),
                  onTap: () {
                    Navigator.of(sheetContext).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const MobileFrame(child: PastProgramsScreen())),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.ios_share, color: AppColors.textDark),
                  title: const Text('Share with someone', style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark)),
                  onTap: () {
                    Navigator.of(sheetContext).pop();
                    final provider = context.read<ProgramProvider>();
                    ShareService.instance.shareText(
                      "My weekly care program on MindCare: ${provider.totalDone} of ${provider.totalTasks} tasks done this week.",
                      subject: 'My MindCare program',
                    );
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

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
                    Material(
                      color: Colors.transparent,
                      shape: const CircleBorder(),
                      clipBehavior: Clip.antiAlias,
                      child: InkWell(
                        onTap: () => _showMoreOptions(context),
                        child: const SizedBox(
                          width: 42,
                          height: 42,
                          child: Icon(Icons.more_horiz, color: AppColors.textDark),
                        ),
                      ),
                    ),
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
                            Text("Updated 3 days ago · next review on Friday's session", style: AppTextStyles.body(size: 12)),
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
                GestureDetector(
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const MobileFrame(child: RequestChangeScreen())),
                  ),
                  child: Row(
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