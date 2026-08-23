import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/onboarding_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/common/step_progress_bar.dart';
import '../../widgets/onboarding/selectable_chip.dart';

class YourStoryScreen extends StatefulWidget {
  const YourStoryScreen({super.key});

  @override
  State<YourStoryScreen> createState() => _YourStoryScreenState();
}

class _YourStoryScreenState extends State<YourStoryScreen> {
  static const _concerns = [
    'Anxiety', 'Depression', 'Sleep', 'Stress',
    'Burnout', 'Relationships', 'Grief',
    'Self-esteem', 'Trauma', 'Addiction', 'Family',
    'Identity', 'Work', 'Body image', 'Faith',
  ];

  bool _submitting = false;

  Future<void> _finishSetup(OnboardingProvider provider) async {
    setState(() => _submitting = true);
    await provider.finishSetup();
    if (!mounted) return;
    setState(() => _submitting = false);
    Navigator.of(context).pushNamedAndRemoveUntil('/home', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<OnboardingProvider>();

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: ListView(
            children: [
              const SizedBox(height: 12),
              const StepProgressBar(currentStep: 3, totalSteps: 3),
              const SizedBox(height: 28),
              Text.rich(
                TextSpan(
                  style: AppTextStyles.heading(size: 30),
                  children: [
                    const TextSpan(text: 'A little about\n'),
                    TextSpan(text: 'your story.', style: AppTextStyles.heading(size: 30, style: FontStyle.italic)),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text('This helps us match you with the right care. You can skip anything.', style: AppTextStyles.body()),
              const SizedBox(height: 24),
              Text('SPOKEN WITH A THERAPIST BEFORE?', style: AppTextStyles.label()),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(color: AppColors.progressTrack.withOpacity(0.5), borderRadius: BorderRadius.circular(18)),
                child: Row(
                  children: ['Never', 'Yes, once or twice', 'In therapy now'].map((option) {
                    final selected = provider.data.therapistHistory == option;
                    return Expanded(
                      child: GestureDetector(
                        onTap: () => context.read<OnboardingProvider>().setTherapistHistory(option),
                        child: Container(
                          margin: const EdgeInsets.symmetric(horizontal: 3),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: selected ? Colors.white : Colors.transparent,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Text(
                            option,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                              color: AppColors.textDark,
                            ),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
                decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(18)),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Currently on medication', style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark)),
                          const SizedBox(height: 2),
                          Text('For mental health (optional)', style: AppTextStyles.body(size: 13)),
                        ],
                      ),
                    ),
                    Switch(
                      value: provider.data.onMedication,
                      activeColor: AppColors.primaryDark,
                      onChanged: (value) => context.read<OnboardingProvider>().setOnMedication(value),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 22),
              Text("WHAT'S BEEN ON YOUR MIND?", style: AppTextStyles.label()),
              const SizedBox(height: 12),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: _concerns.map((concern) {
                  final selected = provider.data.concerns.contains(concern);
                  return SelectableChip(
                    label: concern,
                    selected: selected,
                    onTap: () => context.read<OnboardingProvider>().toggleConcern(concern),
                  );
                }).toList(),
              ),
              const SizedBox(height: 22),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.shield_outlined, size: 18, color: AppColors.infoBoxText),
                    const SizedBox(width: 10),
                    Expanded(
                      child: RichText(
                        text: const TextSpan(
                          style: TextStyle(color: AppColors.infoBoxText, fontSize: 13, height: 1.4),
                          children: [
                            TextSpan(text: 'End-to-end private. ', style: TextStyle(fontWeight: FontWeight.w700)),
                            TextSpan(text: 'Your answers are encrypted. Only the therapist you choose can see them.'),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 26),
              Row(
                children: [
                  Expanded(
                    child: PrimaryButton(
                      label: 'Finish setup',
                      icon: null,
                      loading: _submitting,
                      onPressed: () => _finishSetup(context.read<OnboardingProvider>()),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const SosButton(),
                ],
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}