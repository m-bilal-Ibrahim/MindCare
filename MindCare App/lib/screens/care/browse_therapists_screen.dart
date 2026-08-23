import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/care/therapist_card.dart';
import '../../widgets/common/sos_button.dart';
import 'plan_trial_screen.dart';

class BrowseTherapistsScreen extends StatelessWidget {
  const BrowseTherapistsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TherapyProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 110),
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('CARE', style: AppTextStyles.label()),
                          const SizedBox(height: 6),
                          Text('Find your person.', style: AppTextStyles.heading(size: 28)),
                        ],
                      ),
                    ),
                    Container(
                      width: 42,
                      height: 42,
                      decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                      child: const Icon(Icons.tune, color: AppColors.textDark, size: 18),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                  child: TextField(
                    onChanged: (value) => context.read<TherapyProvider>().setSearchQuery(value),
                    decoration: const InputDecoration(
                      icon: Icon(Icons.search, color: AppColors.textMuted),
                      border: InputBorder.none,
                      hintText: 'Search by specialty, language...',
                      contentPadding: EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                SizedBox(
                  height: 38,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: TherapyProvider.filterChips.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final chip = TherapyProvider.filterChips[index];
                      final selected = provider.selectedFilter == chip;
                      return GestureDetector(
                        onTap: () => context.read<TherapyProvider>().setFilter(chip),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 18),
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: selected ? AppColors.chipSelected : AppColors.chipUnselected,
                            borderRadius: BorderRadius.circular(30),
                          ),
                          child: Text(
                            chip,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: selected ? Colors.white : AppColors.chipTextUnselected,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(18)),
                  child: Row(
                    children: [
                      const Icon(Icons.auto_awesome, size: 18, color: AppColors.infoBoxText),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("Aida's matches for you", style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.infoBoxText)),
                            const SizedBox(height: 2),
                            Text('Based on your intake — Anxiety, Burnout, Sleep', style: TextStyle(fontSize: 12, color: AppColors.infoBoxText)),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right, color: AppColors.infoBoxText),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                ...provider.filteredTherapists.map(
                  (therapist) => TherapistCard(
                    therapist: therapist,
                    onViewPlan: () {
                      context.read<TherapyProvider>().selectTherapist(therapist);
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const MobileFrame(child: PlanTrialScreen())),
                      );
                    },
                  ),
                ),
              ],
            ),
            const Positioned(right: 0, bottom: 90, child: SosButton()),
          ],
        ),
      ),
    );
  }
}