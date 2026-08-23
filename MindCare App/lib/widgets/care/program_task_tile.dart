import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/program_data.dart';

class ProgramTaskTile extends StatelessWidget {
  const ProgramTaskTile({super.key, required this.task});
  final WeeklyTask task;

  @override
  Widget build(BuildContext context) {
    final progress = task.total == 0 ? 0.0 : task.done / task.total;
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(color: task.color, borderRadius: BorderRadius.circular(14)),
            child: const Icon(Icons.play_arrow, color: Colors.white, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(task.category, style: const TextStyle(fontSize: 11, letterSpacing: 0.5, color: AppColors.textLabel, fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text(task.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.textDark)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: progress,
                          minHeight: 6,
                          backgroundColor: AppColors.progressTrack,
                          valueColor: AlwaysStoppedAnimation(task.color),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text('${task.done}/${task.total}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}