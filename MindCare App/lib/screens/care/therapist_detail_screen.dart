import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/account_provider.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/common/primary_button.dart';
import 'browse_therapists_screen.dart';
import 'message_therapist_screen.dart';
import 'reschedule_screen.dart';
import 'schedule_screen.dart';

class TherapistDetailScreen extends StatelessWidget {
  const TherapistDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final therapist = context.watch<AccountProvider>().therapistProfile;
    final hasActiveTherapist = context.watch<TherapyProvider>().selectedTherapist != null;

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
                    'YOUR THERAPIST',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 12),
            Center(
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 42,
                    backgroundColor: AppColors.moodStressed,
                    child: Text(
                      therapist.name.split(' ').where((w) => w.isNotEmpty && w != 'Dr.').take(2).map((w) => w[0]).join(),
                      style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w700),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(therapist.name, style: AppTextStyles.heading(size: 22)),
                  const SizedBox(height: 4),
                  Text(therapist.credentials, style: AppTextStyles.body(size: 13)),
                  const SizedBox(height: 4),
                  Text(therapist.since, style: AppTextStyles.body(size: 12)),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.star, size: 16, color: Color(0xFFCB8B57)),
                      const SizedBox(width: 4),
                      Text('${therapist.rating}', style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark, fontSize: 13)),
                      const SizedBox(width: 12),
                      Text('${therapist.sessionsWithYou} sessions with you', style: AppTextStyles.body(size: 12)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => MobileFrame(child: MessageTherapistScreen(therapistName: therapist.name))),
                    ),
                    icon: const Icon(Icons.chat_bubble_outline, size: 16, color: AppColors.textDark),
                    label: const Text('Message', style: TextStyle(color: AppColors.textDark)),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      side: const BorderSide(color: AppColors.border),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {
                      if (hasActiveTherapist) {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const MobileFrame(child: RescheduleScreen())),
                        );
                      } else {
                        // No active booking to reschedule — send them
                        // to view/confirm a plan first.
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const MobileFrame(child: ScheduleScreen())),
                        );
                      }
                    },
                    icon: const Icon(Icons.calendar_today_outlined, size: 16, color: AppColors.textDark),
                    label: const Text('Reschedule', style: TextStyle(color: AppColors.textDark)),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      side: const BorderSide(color: AppColors.border),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Text('ABOUT', style: AppTextStyles.label()),
            const SizedBox(height: 10),
            Text(therapist.bio, style: const TextStyle(fontSize: 14, color: AppColors.textDark, height: 1.5)),
            const SizedBox(height: 22),
            Text('SPECIALTIES', style: AppTextStyles.label()),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: therapist.specialties.map((s) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                  child: Text(s, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textDark)),
                );
              }).toList(),
            ),
            const SizedBox(height: 22),
            Text('LANGUAGES', style: AppTextStyles.label()),
            const SizedBox(height: 10),
            Text(therapist.languages.join(' · '), style: const TextStyle(fontSize: 14, color: AppColors.textDark)),
            const SizedBox(height: 28),
            PrimaryButton(
              label: 'Book another session',
              icon: null,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MobileFrame(child: BrowseTherapistsScreen())),
              ),
            ),
          ],
        ),
      ),
    );
  }
}