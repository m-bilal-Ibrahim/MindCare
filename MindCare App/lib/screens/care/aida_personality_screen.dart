import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/primary_button.dart';

class AidaPersonalityScreen extends StatefulWidget {
  const AidaPersonalityScreen({super.key});

  @override
  State<AidaPersonalityScreen> createState() => _AidaPersonalityScreenState();
}

class _AidaPersonalityScreenState extends State<AidaPersonalityScreen> {
  late String _selected;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _selected = context.read<AccountProvider>().aidaPersonality;
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();
    final hasChanged = _selected != provider.aidaPersonality;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 20),
                children: [
                  Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                      ),
                      const Expanded(
                        child: Text(
                          'AIDA PERSONALITY',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('How should Aida talk with you?', style: AppTextStyles.heading(size: 24)),
                  const SizedBox(height: 8),
                  Text('You can change this anytime. It only changes tone, never the care itself.', style: AppTextStyles.body()),
                  const SizedBox(height: 20),
                  ...provider.aidaPersonalityOptions.map((option) {
                    final isSelected = _selected == option.name;
                    return GestureDetector(
                      onTap: () => setState(() => _selected = option.name),
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: isSelected ? AppColors.textDark : Colors.transparent, width: 1.6),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 44,
                              height: 44,
                              decoration: BoxDecoration(color: option.color.withOpacity(0.15), borderRadius: BorderRadius.circular(14)),
                              child: Icon(option.icon, color: option.color, size: 22),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(option.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.textDark)),
                                      if (option.name == provider.aidaPersonality) ...[
                                        const SizedBox(width: 8),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(10)),
                                          child: const Text('CURRENT', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.progressActive)),
                                        ),
                                      ],
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(option.tagline, style: const TextStyle(fontSize: 12, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
                                  const SizedBox(height: 6),
                                  Text(option.description, style: const TextStyle(fontSize: 12.5, color: AppColors.textMuted, height: 1.4)),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              width: 22,
                              height: 22,
                              margin: const EdgeInsets.only(top: 2),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isSelected ? AppColors.textDark : Colors.transparent,
                                border: isSelected ? null : Border.all(color: AppColors.border, width: 1.5),
                              ),
                              child: isSelected ? const Icon(Icons.check, size: 14, color: Colors.white) : null,
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
              child: PrimaryButton(
                label: hasChanged ? 'Save' : 'No changes to save',
                icon: null,
                loading: _saving,
                onPressed: !hasChanged
                    ? null
                    : () async {
                        setState(() => _saving = true);
                        await Future.delayed(const Duration(milliseconds: 400));
                        if (!mounted) return;
                        context.read<AccountProvider>().setAidaPersonality(_selected);
                        setState(() => _saving = false);
                        Navigator.of(context).maybePop();
                      },
              ),
            ),
          ],
        ),
      ),
    );
  }
}