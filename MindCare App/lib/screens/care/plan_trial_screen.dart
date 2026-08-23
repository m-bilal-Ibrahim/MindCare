import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/care/benefit_row.dart';
import '../../widgets/care/plan_option_tile.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';
import 'schedule_screen.dart';
import 'your_program_screen.dart';

class PlanTrialScreen extends StatelessWidget {
  const PlanTrialScreen({super.key});

  String _formatPrice(int price) {
    final s = price.toString();
    final buffer = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i != 0 && (s.length - i) % 3 == 0) buffer.write(',');
      buffer.write(s[i]);
    }
    return buffer.toString();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TherapyProvider>();
    final therapist = provider.selectedTherapist;

    if (therapist == null) {
      return const Scaffold(body: Center(child: Text('No therapist selected')));
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 130),
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    Row(
                      children: [
                        _CircleIconButton(icon: Icons.bookmark_border, onTap: () {}),
                        const SizedBox(width: 10),
                        _CircleIconButton(icon: Icons.ios_share, onTap: () {}),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 32,
                      backgroundColor: therapist.avatarColor,
                      child: Text(therapist.initials, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(therapist.name, style: AppTextStyles.heading(size: 22)),
                          const SizedBox(height: 4),
                          Text(therapist.title, style: AppTextStyles.body(size: 13)),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              const Icon(Icons.star, size: 14, color: Color(0xFFC79A56)),
                              const SizedBox(width: 4),
                              Text('${therapist.rating}', style: AppTextStyles.body(size: 13, color: AppColors.textDark)),
                              Text('  ·  ${therapist.reviewCount} reviews  ·  ${therapist.credentialBadge}', style: AppTextStyles.body(size: 13)),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                if (therapist.trialAvailable)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [Color(0xFFF0DEB9), Color(0xFFE1E6DC)]),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(color: AppColors.amberSegment, borderRadius: BorderRadius.circular(12)),
                          child: const Icon(Icons.eco_outlined, color: Colors.white, size: 18),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Try ${therapist.name} for 7 days, free.', style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                              const SizedBox(height: 4),
                              Text('One intake call + chat access. Cancel any time during trial — no charge.', style: AppTextStyles.body(size: 13)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 24),
                Text('CHOOSE YOUR PLAN', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                PlanOptionTile(
                  selected: provider.selectedPlanId == 'monthly',
                  title: 'Monthly',
                  subtitle: '4 sessions + chat + program updates',
                  price: 'Rs ${_formatPrice(therapist.priceMonthly)}',
                  priceUnit: '/ month',
                  onTap: () => context.read<TherapyProvider>().selectPlan('monthly'),
                ),
                PlanOptionTile(
                  selected: provider.selectedPlanId == 'yearly',
                  title: 'Yearly',
                  subtitle: '48 sessions · save Rs ${_formatPrice(therapist.priceMonthly * 2)} · pause any time',
                  price: 'Rs ${_formatPrice(therapist.priceYearly)}',
                  priceUnit: '/ year',
                  badge: '2 months free',
                  onTap: () => context.read<TherapyProvider>().selectPlan('yearly'),
                ),
                const SizedBox(height: 20),
                Text('WHAT YOU GET', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                Container(
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                  child: Column(
                    children: [
                      const BenefitRow(
                        icon: Icons.videocam_outlined,
                        title: 'Weekly 50-min video sessions',
                        subtitle: 'Reschedule freely with notice.',
                      ),
                      const BenefitRow(
                        icon: Icons.chat_bubble_outline,
                        title: 'In-between chat with your therapist',
                        subtitle: '48-hour response, weekdays.',
                      ),
                      BenefitRow(
                        icon: Icons.auto_awesome,
                        title: 'Your permanent care program',
                        subtitle: 'Updated by your therapist from time to time.',
                        showDivider: false,
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const MobileFrame(child: YourProgramScreen())),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            Positioned(
              left: 24,
              right: 24,
              bottom: 16,
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: PrimaryButton(
                          label: therapist.trialAvailable ? 'Start 7-day free trial' : 'Choose this plan',
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const MobileFrame(child: ScheduleScreen())),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const SosButton(),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('Then Rs ${_formatPrice(therapist.priceMonthly)} / month. Cancel any time.', style: AppTextStyles.body(size: 11)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CircleIconButton extends StatelessWidget {
  const _CircleIconButton({required this.icon, required this.onTap});
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 42,
        height: 42,
        decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
        child: Icon(icon, size: 18, color: AppColors.textDark),
      ),
    );
  }
}