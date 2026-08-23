import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/account_data.dart';

class ProfileListSection extends StatelessWidget {
  const ProfileListSection({super.key, required this.items, this.onItemTap});
  final List<ProfileListItem> items;
  final void Function(int index)? onItemTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        children: List.generate(items.length, (i) {
          final item = items[i];
          return Column(
            children: [
              InkWell(
                onTap: onItemTap != null ? () => onItemTap!(i) : null,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(10)),
                        child: Icon(item.icon, size: 17, color: AppColors.textDark),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(item.title, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark, fontSize: 14)),
                            if (item.subtitle != null) ...[
                              const SizedBox(height: 2),
                              Text(item.subtitle!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                            ],
                          ],
                        ),
                      ),
                      if (item.trailing != null) ...[
                        Text(item.trailing!, style: const TextStyle(fontSize: 13, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
                        const SizedBox(width: 6),
                      ],
                      const Icon(Icons.chevron_right, size: 18, color: AppColors.textMuted),
                    ],
                  ),
                ),
              ),
              if (item.showDivider) const Divider(height: 1, indent: 16, endIndent: 16, color: AppColors.border),
            ],
          );
        }),
      ),
    );
  }
}
