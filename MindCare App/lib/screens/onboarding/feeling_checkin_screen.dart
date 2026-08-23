import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/onboarding_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/common/step_progress_bar.dart';
import '../../widgets/onboarding/mood_card.dart';
import 'your_story_screen.dart';

class FeelingCheckinScreen extends StatelessWidget {
  const FeelingCheckinScreen({super.key});

  static const List<MoodOption> _moods = [
    MoodOption('Calm', AppColors.moodCalm),
    MoodOption('Content', AppColors.moodContent),
    MoodOption('Stressed', AppColors.moodStressed),
    MoodOption('Anxious', AppColors.moodAnxious),
    MoodOption('Low', AppColors.moodLow),
    MoodOption('Numb', AppColors.moodNumb),
    MoodOption('Angry', AppColors.moodAngry),
    MoodOption('Hopeful', AppColors.moodHopeful),
    MoodOption('Tired', AppColors.moodTired),
  ];

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<OnboardingProvider>();
    final selectedCount = provider.data.selectedMoods.length;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: ListView(
            children: [
              const SizedBox(height: 12),
              const StepProgressBar(currentStep: 2, totalSteps: 3),
              const SizedBox(height: 28),
              Text.rich(
                TextSpan(
                  style: AppTextStyles.heading(size: 30),
                  children: [
                    const TextSpan(text: 'How have you\n'),
                    TextSpan(text: 'been feeling', style: AppTextStyles.heading(size: 30, style: FontStyle.italic)),
                    const TextSpan(text: ' lately?'),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text("Pick any that fit. There's no wrong answer — and you can change this any time.", style: AppTextStyles.body()),
              const SizedBox(height: 24),
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _moods.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 0.82,
                ),
                itemBuilder: (context, index) {
                  final mood = _moods[index];
                  final selected = provider.data.selectedMoods.contains(mood.label);
                  return MoodCard(
                    option: mood,
                    selected: selected,
                    onTap: () => context.read<OnboardingProvider>().toggleMood(mood.label),
                  );
                },
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(20)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('RIGHT NOW, HOW STRONG IS IT?', style: AppTextStyles.label()),
                    Slider(
                      value: provider.data.intensity,
                      onChanged: (value) => context.read<OnboardingProvider>().setIntensity(value),
                      activeColor: AppColors.moodStressed,
                      inactiveColor: AppColors.progressTrack,
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('gentle', style: AppTextStyles.body(size: 13)),
                        Text('heavy', style: AppTextStyles.body(size: 13)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 26),
              Row(
                children: [
                  Expanded(
                    child: PrimaryButton(
                      label: selectedCount > 0 ? 'Continue · $selectedCount selected' : 'Continue',
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const MobileFrame(child: YourStoryScreen())),
                      ),
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