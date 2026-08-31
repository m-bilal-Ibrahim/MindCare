import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/community_data.dart';
import '../../providers/community_provider.dart';

Future<void> showPostOptionsSheet(
  BuildContext context, {
  required CommunityProvider provider,
  required CommunityPost post,
}) {
  return showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (sheetContext) {
      return SafeArea(
        child: Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                margin: const EdgeInsets.symmetric(vertical: 10),
                width: 40,
                height: 4,
                decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(4)),
              ),
              _SheetOption(
                icon: Icons.flag_outlined,
                label: 'Report post',
                onTap: () {
                  provider.reportPost(post.id);
                  Navigator.of(sheetContext).pop();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Reported. Our team will review this.')),
                  );
                },
              ),
              _SheetOption(
                icon: Icons.visibility_off_outlined,
                label: 'Hide this post',
                onTap: () {
                  provider.hidePost(post.id);
                  Navigator.of(sheetContext).pop();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Hidden. You won't see this post again.")),
                  );
                },
              ),
              if (!post.isAnonymous)
                _SheetOption(
                  icon: Icons.block,
                  label: 'Block ${post.handle}',
                  isDestructive: true,
                  onTap: () {
                    provider.blockUser(post.handle);
                    Navigator.of(sheetContext).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('${post.handle} is blocked. You won\'t see their posts.')),
                    );
                  },
                ),
              _SheetOption(
                icon: Icons.close,
                label: 'Cancel',
                onTap: () => Navigator.of(sheetContext).pop(),
              ),
              const SizedBox(height: 6),
            ],
          ),
        ),
      );
    },
  );
}

class _SheetOption extends StatelessWidget {
  const _SheetOption({required this.icon, required this.label, required this.onTap, this.isDestructive = false});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool isDestructive;

  @override
  Widget build(BuildContext context) {
    final color = isDestructive ? AppColors.sos : AppColors.textDark;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(width: 16),
            Text(label, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: color)),
          ],
        ),
      ),
    );
  }
}