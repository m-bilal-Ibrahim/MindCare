import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/therapy_data.dart';

class SlotTile extends StatelessWidget {
  const SlotTile({super.key, required this.slot, required this.selected, required this.onTap});
  final ScheduleSlot slot;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isOff = slot.status == 'off';
    final isBooked = slot.status == 'booked';
    final isFree = slot.status == 'free';

    Color background = Colors.white;
    Color textColor = AppColors.textDark;
    if (selected) {
      background = AppColors.progressActive;
      textColor = Colors.white;
    } else if (isBooked || isOff) {
      textColor = AppColors.textMuted;
    }

    return GestureDetector(
      onTap: isFree ? onTap : null,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: background,
          borderRadius: BorderRadius.circular(16),
          border: isOff ? Border.all(color: AppColors.border) : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(slot.time, style: TextStyle(fontWeight: FontWeight.w600, color: textColor)),
            Text('· ${slot.status}', style: TextStyle(fontSize: 12, color: selected ? Colors.white70 : AppColors.textMuted)),
          ],
        ),
      ),
    );
  }
}