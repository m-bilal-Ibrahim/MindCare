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

  void _showFilters(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        final therapy = context.read<TherapyProvider>();
        return SafeArea(
          child: StatefulBuilder(
            builder: (sheetContext, setSheetState) {
              return Padding(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 18), decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2))),
                    ),
                    Text('Sort & filter', style: AppTextStyles.heading(size: 20)),
                    const SizedBox(height: 16),
                    _SheetOption(
                      icon: Icons.star_outline,
                      label: 'Highest rated first',
                      selected: therapy.sortMode == 'rating',
                      onTap: () {
                        therapy.setSortMode('rating');
                        Navigator.of(sheetContext).pop();
                      },
                    ),
                    _SheetOption(
                      icon: Icons.attach_money,
                      label: 'Price: low to high',
                      selected: therapy.sortMode == 'price_low',
                      onTap: () {
                        therapy.setSortMode('price_low');
                        Navigator.of(sheetContext).pop();
                      },
                    ),
                    _SheetOption(
                      icon: Icons.eco_outlined,
                      label: '7-day trial available',
                      selected: therapy.sortMode == 'trial',
                      onTap: () {
                        therapy.setSortMode('trial');
                        Navigator.of(sheetContext).pop();
                      },
                    ),
                    if (therapy.sortMode != 'default') ...[
                      const SizedBox(height: 16),
                      Center(
                        child: TextButton(
                          onPressed: () {
                            therapy.setSortMode('default');
                            Navigator.of(sheetContext).pop();
                          },
                          child: const Text('Clear sort & filter', style: TextStyle(color: AppColors.sos, fontWeight: FontWeight.w600)),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

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
                    Material(
                      color: Colors.white,
                      shape: const CircleBorder(),
                      clipBehavior: Clip.antiAlias,
                      child: InkWell(
                        onTap: () => _showFilters(context),
                        child: SizedBox(
                          width: 42,
                          height: 42,
                          child: Icon(
                            Icons.tune,
                            color: provider.sortMode != 'default' ? AppColors.progressActive : AppColors.textDark,
                            size: 18,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                if (provider.sortMode != 'default') ...[
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerRight,
                    child: Text(_sortLabel(provider), style: const TextStyle(fontSize: 12, color: AppColors.progressActive, fontWeight: FontWeight.w600)),
                  ),
                ],
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
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                if (provider.filteredTherapists.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 40),
                    child: Column(
                      children: [
                        const Icon(Icons.search_off, size: 32, color: AppColors.textMuted),
                        const SizedBox(height: 12),
                        Text('No therapists match this filter.', style: AppTextStyles.body()),
                      ],
                    ),
                  )
                else
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

  String _sortLabel(TherapyProvider provider) {
    switch (provider.sortMode) {
      case 'rating':
        return 'Sorted by rating';
      case 'price_low':
        return 'Sorted by price';
      case 'trial':
        return 'Trial available only';
      default:
        return '';
    }
  }
}

class _SheetOption extends StatelessWidget {
  const _SheetOption({required this.icon, required this.label, required this.onTap, this.selected = false});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 19, color: selected ? AppColors.progressActive : AppColors.textDark),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: TextStyle(fontSize: 14, color: selected ? AppColors.progressActive : AppColors.textDark, fontWeight: selected ? FontWeight.w700 : FontWeight.w500),
              ),
            ),
            if (selected) const Icon(Icons.check, size: 18, color: AppColors.progressActive),
          ],
        ),
      ),
    );
  }
}