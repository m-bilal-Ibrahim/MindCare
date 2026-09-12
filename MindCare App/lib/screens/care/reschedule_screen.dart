import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../models/therapy_data.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/care/day_chip.dart';
import '../../widgets/care/slot_tile.dart';
import '../../widgets/common/primary_button.dart';

class RescheduleScreen extends StatefulWidget {
  const RescheduleScreen({super.key});

  @override
  State<RescheduleScreen> createState() => _RescheduleScreenState();
}

class _RescheduleScreenState extends State<RescheduleScreen> {
  int _dayIndex = 2;
  String? _slotTime;
  bool _saving = false;
  bool _done = false;

  static const _slots = [
    ScheduleSlot('9:30 AM', 'booked'),
    ScheduleSlot('11:00 AM', 'free'),
    ScheduleSlot('12:30 PM', 'free'),
    ScheduleSlot('2:00 PM', 'booked'),
    ScheduleSlot('3:30 PM', 'free'),
    ScheduleSlot('5:00 PM', 'free'),
    ScheduleSlot('6:30 PM', 'booked'),
    ScheduleSlot('8:00 PM', 'off'),
  ];

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TherapyProvider>();
    final selectedDay = TherapyProvider.weekDays[_dayIndex];

    if (_done) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 84,
                  height: 84,
                  decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle),
                  child: const Icon(Icons.check, color: Colors.white, size: 36),
                ),
                const SizedBox(height: 24),
                Text('Rescheduled.', style: AppTextStyles.heading(size: 26)),
                const SizedBox(height: 8),
                Text(provider.nextConfirmedLabel, style: AppTextStyles.body(size: 15)),
                const SizedBox(height: 32),
                PrimaryButton(label: 'Done', icon: null, onPressed: () => Navigator.of(context).pop()),
              ],
            ),
          ),
        ),
      );
    }

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
                        icon: const Icon(Icons.close, color: AppColors.textDark),
                      ),
                      const Expanded(
                        child: Text(
                          'RESCHEDULE',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('Currently: ${provider.nextConfirmedLabel}', style: AppTextStyles.body()),
                  const SizedBox(height: 4),
                  Text('Pick a new day and time.', style: AppTextStyles.heading(size: 22)),
                  const SizedBox(height: 20),
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
                          selected: index == _dayIndex,
                          onTap: () => setState(() {
                            _dayIndex = index;
                            _slotTime = null;
                          }),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text('AVAILABILITY', style: AppTextStyles.label()),
                  const SizedBox(height: 12),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 10,
                    crossAxisSpacing: 10,
                    childAspectRatio: 2.6,
                    children: _slots.map((slot) {
                      return SlotTile(
                        slot: slot,
                        selected: _slotTime == slot.time,
                        onTap: () => setState(() => _slotTime = slot.time),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
              child: PrimaryButton(
                label: _slotTime == null
                    ? 'Select a time'
                    : 'Confirm ${selectedDay.label}, May ${selectedDay.date} · $_slotTime',
                icon: null,
                loading: _saving,
                onPressed: _slotTime == null
                    ? null
                    : () async {
                        setState(() => _saving = true);
                        await context.read<TherapyProvider>().rescheduleSession(selectedDay.label, selectedDay.date, _slotTime!);
                        if (!mounted) return;
                        setState(() {
                          _saving = false;
                          _done = true;
                        });
                      },
              ),
            ),
          ],
        ),
      ),
    );
  }
}