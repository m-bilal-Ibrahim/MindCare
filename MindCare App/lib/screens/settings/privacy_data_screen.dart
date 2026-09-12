import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/settings_provider.dart';

class PrivacyDataScreen extends StatefulWidget {
  const PrivacyDataScreen({super.key});

  @override
  State<PrivacyDataScreen> createState() => _PrivacyDataScreenState();
}

class _PrivacyDataScreenState extends State<PrivacyDataScreen> {
  bool _exporting = false;

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SettingsProvider>();

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
                    'PRIVACY & DATA',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('What your therapist sees.', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 8),
            Text('Control exactly what gets shared, and with whom.', style: AppTextStyles.body()),
            const SizedBox(height: 22),
            Container(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
              child: Column(
                children: List.generate(provider.privacyToggles.length, (i) {
                  final toggle = provider.privacyToggles[i];
                  return Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(toggle.title, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark, fontSize: 14)),
                                      if (toggle.locked) ...[
                                        const SizedBox(width: 6),
                                        const Icon(Icons.lock, size: 13, color: AppColors.textMuted),
                                      ],
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(toggle.subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted, height: 1.3)),
                                ],
                              ),
                            ),
                            Switch(
                              value: toggle.enabled,
                              activeThumbColor: AppColors.primaryDark,
                              onChanged: toggle.locked ? null : (_) => context.read<SettingsProvider>().togglePrivacy(toggle.id),
                            ),
                          ],
                        ),
                      ),
                      if (i != provider.privacyToggles.length - 1) const Divider(height: 1, indent: 16, endIndent: 16, color: AppColors.border),
                    ],
                  );
                }),
              ),
            ),
            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(18)),
              child: Row(
                children: [
                  const Icon(Icons.shield_outlined, size: 18, color: AppColors.infoBoxText),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Your data is encrypted at rest and in transit. Only your therapist and Aida can see what you\'ve chosen to share above — never other users.',
                      style: TextStyle(fontSize: 12, color: AppColors.infoBoxText, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 22),
            _ActionRow(
              icon: Icons.download_outlined,
              label: 'Export my data',
              loading: _exporting,
              onTap: () async {
                setState(() => _exporting = true);
                await context.read<SettingsProvider>().requestDataExport();
                if (!mounted) return;
                setState(() => _exporting = false);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("We'll email you a secure download link shortly.")),
                );
              },
            ),
            const SizedBox(height: 10),
            _ActionRow(
              icon: Icons.delete_outline,
              label: 'Delete my account',
              isDestructive: true,
              onTap: () => _confirmDeleteAccount(context),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDeleteAccount(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppColors.background,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Delete your account?', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
        content: Text('This permanently removes your data and cannot be undone.', style: AppTextStyles.body(size: 14)),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text('Delete', style: TextStyle(color: AppColors.sos, fontWeight: FontWeight.w700))),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account deletion isn\'t wired to a backend yet.')),
      );
    }
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({required this.icon, required this.label, required this.onTap, this.isDestructive = false, this.loading = false});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool isDestructive;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final color = isDestructive ? AppColors.sos : AppColors.textDark;
    return GestureDetector(
      onTap: loading ? null : onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (loading)
              const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
            else
              Icon(icon, size: 18, color: color),
            const SizedBox(width: 10),
            Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 14)),
          ],
        ),
      ),
    );
  }
}