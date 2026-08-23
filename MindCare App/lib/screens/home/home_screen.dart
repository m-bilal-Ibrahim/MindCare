import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/checkin_provider.dart';
import '../../widgets/home/home_action_cards.dart';
import '../../widgets/home/mood_selector.dart';
import '../../widgets/home/vitals_card.dart';
import 'aida_chat_screen.dart';
import 'progress_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  String _formattedDate() {
    const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    final now = DateTime.now();
    final weekday = weekdays[now.weekday - 1];
    final month = months[now.month - 1];
    return '$weekday, $month ${now.day}'.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 110),
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_formattedDate(), style: AppTextStyles.label()),
                      const SizedBox(height: 6),
                      Text.rich(
                        TextSpan(
                          style: AppTextStyles.heading(size: 28),
                          children: [
                            const TextSpan(text: 'Good morning, '),
                            TextSpan(text: 'Layla.', style: AppTextStyles.heading(size: 28, style: FontStyle.italic)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Container(
                      width: 42,
                      height: 42,
                      decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                      child: const Icon(Icons.notifications_outlined, color: AppColors.textDark, size: 20),
                    ),
                    Positioned(
                      top: 0,
                      right: 0,
                      child: Container(
                        width: 10,
                        height: 10,
                        decoration: const BoxDecoration(color: AppColors.sos, shape: BoxShape.circle),
                      ),
                    ),
                  ],
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const MobileFrame(child: ProgressScreen())),
                  ),
                  child: const CircleAvatar(
                    radius: 21,
                    backgroundColor: AppColors.sos,
                    child: Text('L', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(24)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("TODAY'S CHECK-IN", style: AppTextStyles.label()),
                  const SizedBox(height: 10),
                  Text('How are you arriving into the day?', style: AppTextStyles.heading(size: 22)),
                  const SizedBox(height: 18),
                  const MoodSelector(),
                ],
              ),
            ),
            const SizedBox(height: 16),
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(
                    flex: 5,
                    child: AidaListeningCard(
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const MobileFrame(child: AidaChatScreen())),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    flex: 5,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AppointmentCard(),
                        SizedBox(height: 12),
                        QuickBreathCard(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('YOUR BODY TODAY', style: AppTextStyles.label()),
                Consumer<CheckinProvider>(
                  builder: (_, provider, __) => Row(
                    children: [
                      const Icon(Icons.circle, size: 8, color: AppColors.progressActive),
                      const SizedBox(width: 6),
                      Text(provider.vitals.state, style: AppTextStyles.body(size: 13)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const VitalsSummaryCard(),
            const SizedBox(height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('FOR YOU, TODAY', style: AppTextStyles.label()),
                Text('see all', style: AppTextStyles.body(size: 13, weight: FontWeight.w600, color: AppColors.textDark)),
              ],
            ),
            const SizedBox(height: 12),
            const ActionPillRow(),
          ],
        ),
      ),
    );
  }
}