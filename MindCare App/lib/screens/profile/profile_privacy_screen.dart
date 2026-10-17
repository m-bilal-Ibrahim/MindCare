import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../models/profile_data.dart';
import '../../providers/profile_provider.dart';
import '../../widgets/common/skeleton.dart';
import '../../widgets/profile/profile_widgets.dart';

/// One switch (is_profile_public) with exactly what it shows and what always
/// stays private, as listed by the backend.
class ProfilePrivacyScreen extends StatefulWidget {
  const ProfilePrivacyScreen({super.key});

  @override
  State<ProfilePrivacyScreen> createState() => _ProfilePrivacyScreenState();
}

class _ProfilePrivacyScreenState extends State<ProfilePrivacyScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<ProfileProvider>().ensureLoaded();
    });
  }

  static String _label(String key) => switch (key) {
        'full_name' => 'Your real name',
        'photo' => 'Your profile photo',
        _ => profilePartLabels[key] ?? key,
      };

  Future<void> _toggle(PatientProfile p, bool makePublic) async {
    if (makePublic) {
      final ok = await showDialog<bool>(
        context: context,
        builder: (d) => AlertDialog(
          backgroundColor: AppColors.background,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Text('Show your real name?', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
          content: Text(
            'Other people will see your real name and photo instead of "${p.pseudonym}". '
            'Anyone who sees them while your profile is public may still recognise you later, even if you switch back to private.',
            style: AppTextStyles.body(size: 14),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(d, false), child: const Text('Stay private', style: TextStyle(color: AppColors.textMuted))),
            TextButton(onPressed: () => Navigator.pop(d, true), child: const Text('Make public', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark))),
          ],
        ),
      );
      if (ok != true || !mounted) return;
    }
    final error = await context.read<ProfileProvider>().update({'is_profile_public': makePublic});
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error?.message ?? (makePublic ? 'Your profile is now public.' : 'Your profile is now private.'))),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProfileProvider>();
    final state = provider.profile;
    final p = state.data;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          children: [
            const ProfileTopBar(label: 'PROFILE VISIBILITY'),
            const SizedBox(height: 8),
            Text('Who sees what.', style: AppTextStyles.heading(size: 28)),
            const SizedBox(height: 6),
            Text('By default other people see a made-up name, not your real one.', style: AppTextStyles.body()),
            const SizedBox(height: 20),
            if (p == null && state.error != null)
              ProfileErrorCard(message: state.error!, sessionExpired: state.sessionExpired, onRetry: provider.load)
            else if (p == null)
              const Shimmer(
                child: Column(
                  children: [
                    SkeletonBox(height: 84, radius: 20),
                    SizedBox(height: 18),
                    SkeletonBox(height: 120, radius: 20),
                    SizedBox(height: 18),
                    SkeletonBox(height: 150, radius: 20),
                  ],
                ),
              )
            else ...[
              Container(
                padding: const EdgeInsets.fromLTRB(18, 8, 8, 8),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Public profile', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark, fontSize: 15)),
                          const SizedBox(height: 2),
                          Text(
                            p.isPublic ? 'Others see "${p.fullName}"' : 'Others see "${p.pseudonym}"',
                            style: AppTextStyles.body(size: 12),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: p.isPublic,
                      activeThumbColor: Colors.white,
                      activeTrackColor: AppColors.progressActive,
                      onChanged: provider.saving ? null : (v) => _toggle(p, v),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              _ListCard(
                title: 'Shown when public',
                icon: Icons.visibility_outlined,
                items: p.shownWhenPublic.map(_label).toList(),
              ),
              const SizedBox(height: 12),
              _ListCard(
                title: 'Always private',
                icon: Icons.lock_outline,
                items: p.alwaysPrivate.map(_label).toList(),
                note: 'Only you and your current psychologist can see these.',
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ListCard extends StatelessWidget {
  const _ListCard({required this.title, required this.icon, required this.items, this.note});
  final String title;
  final IconData icon;
  final List<String> items;
  final String? note;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: AppColors.textDark),
              const SizedBox(width: 8),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
            ],
          ),
          const SizedBox(height: 10),
          for (final i in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  const Icon(Icons.circle, size: 5, color: AppColors.textMuted),
                  const SizedBox(width: 10),
                  Text(i, style: AppTextStyles.body(size: 14, color: AppColors.textDark)),
                ],
              ),
            ),
          if (note != null) ...[
            const SizedBox(height: 4),
            Text(note!, style: AppTextStyles.body(size: 12)),
          ],
        ],
      ),
    );
  }
}
