import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/care/day_chip.dart';
import '../../widgets/care/slot_tile.dart';
import '../../widgets/common/sos_button.dart';
import 'in_session_screen.dart';
import 'your_program_screen.dart';

class ScheduleScreen extends StatelessWidget {
  const ScheduleScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TherapyProvider>();
    final therapist = provider.selectedTherapist;
    if (therapist == null) {
      return const Scaffold(body: Center(child: Text('No therapist selected')));
    }

    final selectedDay = TherapyProvider.weekDays[provider.selectedDayIndex];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 150),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'SCHEDULE',
                        textAlign: TextAlign.center,
                        style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const MobileFrame(child: YourProgramScreen())),
                      ),
                      icon: const Icon(Icons.more_horiz, color: AppColors.textDark),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    CircleAvatar(
                      radius: 24,
                      backgroundColor: therapist.avatarColor,
                      child: Text(therapist.initials, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("${therapist.name.replaceFirst('Dr. ', '')}'s week", style: AppTextStyles.heading(size: 22)),
                          const SizedBox(height: 2),
                          Text(
                            "You're on the monthly plan · ${provider.sessionsUsed} of ${provider.sessionsTotal} sessions used",
                            style: AppTextStyles.body(size: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('NEXT CONFIRMED', style: AppTextStyles.label()),
                                const SizedBox(height: 6),
                                Text('Fri · 5:00 PM', style: AppTextStyles.heading(size: 22)),
                              ],
                            ),
                          ),
                          ElevatedButton.icon(
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => const MobileFrame(child: InSessionScreen())),
                            ),
                            icon: const Icon(Icons.videocam_outlined, size: 16, color: Colors.white),
                            label: const Text('Join Meet', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.progressActive,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text('50 min · Meet link sent to both', style: AppTextStyles.body(size: 12)),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {},
                              style: OutlinedButton.styleFrom(
                                backgroundColor: Colors.white,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                side: BorderSide.none,
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              child: const Text('Reschedule', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600, fontSize: 13)),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {},
                              style: OutlinedButton.styleFrom(
                                backgroundColor: Colors.white,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                side: BorderSide.none,
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              child: const Text('Cancel · with note', style: TextStyle(color: AppColors.sos, fontWeight: FontWeight.w600, fontSize: 13)),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(color: const Color(0xFFF0DEB9), borderRadius: BorderRadius.circular(10)),
                        child: const Icon(Icons.schedule, size: 17, color: AppColors.textDark),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Tue 3:30 PM · awaiting confirmation', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                            const SizedBox(height: 4),
                            Text('Requested 2 hours ago · ${therapist.name} usually replies the same day.', style: AppTextStyles.body(size: 12)),
                          ],
                        ),
                      ),
                      const Text('pending', style: TextStyle(color: AppColors.amberSegment, fontWeight: FontWeight.w600, fontSize: 12)),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                Text('REQUEST ANOTHER · MAY', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                SizedBox(
                  height: 74,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: TherapyProvider.weekDays.length,
                    itemBuilder: (context, index) {
                      final day = TherapyProvider.weekDays[index];
                      return DayChip(
                        label: day.label,
                        date: day.date,
                        selected: index == provider.selectedDayIndex,
                        onTap: () => context.read<TherapyProvider>().selectDay(index),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('AVAILABILITY', style: AppTextStyles.label()),
                    Row(
                      children: const [
                        _LegendDot(color: AppColors.progressActive, label: 'free'),
                        SizedBox(width: 10),
                        _LegendDot(color: AppColors.textMuted, label: 'booked'),
                        SizedBox(width: 10),
                        _LegendDot(color: AppColors.border, label: 'off', outline: true),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 2.6,
                  children: provider.availabilityForSelectedDay.map((slot) {
                    return SlotTile(
                      slot: slot,
                      selected: provider.selectedSlotTime == slot.time,
                      onTap: () => context.read<TherapyProvider>().selectSlot(slot.time, slot.status),
                    );
                  }).toList(),
                ),
              ],
            ),
            if (provider.selectedSlotTime != null)
              Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                child: Container(
                  padding: const EdgeInsets.fromLTRB(24, 14, 24, 20),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Requesting · ${selectedDay.label}, May ${selectedDay.date} · ${provider.selectedSlotTime}',
                              style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark, fontSize: 13),
                            ),
                            const SizedBox(height: 2),
                            Text('Counts as session ${provider.sessionsUsed + 1} of ${provider.sessionsTotal}', style: AppTextStyles.body(size: 12)),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton(
                        onPressed: () => context.read<TherapyProvider>().requestSession(),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primaryDark,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
                        ),
                        child: const Text('Send request', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                      ),
                      const SizedBox(width: 8),
                      const SosButton(),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label, this.outline = false});
  final Color color;
  final String label;
  final bool outline;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: outline ? Colors.transparent : color,
            border: outline ? Border.all(color: color) : null,
          ),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
      ],
    );
  }
}