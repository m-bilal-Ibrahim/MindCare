import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/account_data.dart';

class CircleContactTile extends StatelessWidget {
  const CircleContactTile({super.key, required this.contact, required this.selected, required this.onTap});
  final CircleContact contact;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: selected ? AppColors.textDark : Colors.transparent, width: 1.6),
        ),
        child: Row(
          children: [
            CircleAvatar(radius: 22, backgroundColor: contact.avatarColor, child: Text(contact.name.substring(0, 1), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700))),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(contact.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textDark)),
                  Text(contact.relation, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                ],
              ),
            ),
            if (contact.notified)
              const Icon(Icons.check_circle, color: AppColors.progressActive, size: 20)
            else
              Container(
                width: 22,
                height: 22,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: selected ? AppColors.textDark : Colors.transparent,
                  border: selected ? null : Border.all(color: AppColors.border, width: 1.5),
                ),
                child: selected ? const Icon(Icons.check, size: 14, color: Colors.white) : null,
              ),
          ],
        ),
      ),
    );
  }
}