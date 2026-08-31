import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/settings_provider.dart';

class AppearanceScreen extends StatelessWidget {
  const AppearanceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SettingsProvider>();

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
                    'APPEARANCE',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('Make it comfortable.', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 20),
            Text('TEXT SIZE', style: AppTextStyles.label()),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
              child: Column(
                children: [
                  Text(
                    'How are you arriving into the day?',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18 * provider.textScale, fontFamily: 'serif', color: AppColors.textDark),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: List.generate(SettingsProvider.textSizeLabels.length, (i) {
                      final selected = provider.textSizeIndex == i;
                      return Expanded(
                        child: GestureDetector(
                          onTap: () => context.read<SettingsProvider>().setTextSizeIndex(i),
                          child: Container(
                            margin: EdgeInsets.only(right: i != SettingsProvider.textSizeLabels.length - 1 ? 8 : 0),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: selected ? AppColors.textDark : AppColors.background,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              SettingsProvider.textSizeLabels[i],
                              style: TextStyle(color: selected ? Colors.white : AppColors.textMuted, fontWeight: FontWeight.w600, fontSize: 13),
                            ),
                          ),
                        ),
                      );
                    }),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}