import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';

class PastProgramsScreen extends StatelessWidget {
  const PastProgramsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final programs = context.watch<AccountProvider>().pastPrograms;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 30),
          children: [
            Row(
              children: [
                IconButton(
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                ),
                const Expanded(
                  child: Text(
                    'PAST PROGRAMS',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('Where you\'ve been.', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 6),
            Text('${programs.length} previous programs.', style: AppTextStyles.body()),
            const SizedBox(height: 20),
            if (programs.isEmpty)
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                child: Column(
                  children: [
                    const Icon(Icons.history, size: 32, color: AppColors.textMuted),
                    const SizedBox(height: 12),
                    Text('No past programs yet.', style: AppTextStyles.body()),
                  ],
                ),
              )
            else
              ...programs.map((program) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                  child: Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(12)),
                        child: const Icon(Icons.assignment_outlined, size: 18, color: AppColors.textDark),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(program['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textDark)),
                            const SizedBox(height: 2),
                            Text('${program['period']} · set by ${program['setBy']}', style: AppTextStyles.body(size: 12)),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}