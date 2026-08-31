import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/common/primary_button.dart';

class CancelSessionScreen extends StatefulWidget {
  const CancelSessionScreen({super.key});

  @override
  State<CancelSessionScreen> createState() => _CancelSessionScreenState();
}

class _CancelSessionScreenState extends State<CancelSessionScreen> {
  final _noteController = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TherapyProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.close, color: AppColors.textDark),
                  ),
                  const Expanded(
                    child: Text(
                      'CANCEL SESSION',
                      textAlign: TextAlign.center,
                      style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
              Expanded(
                child: ListView(
                  children: [
                    const SizedBox(height: 8),
                    Text('Cancel ${provider.nextConfirmedLabel}?', style: AppTextStyles.heading(size: 24)),
                    const SizedBox(height: 8),
                    Text('A short note helps your therapist plan around it — totally optional.', style: AppTextStyles.body()),
                    const SizedBox(height: 20),
                    Container(
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                      child: TextField(
                        controller: _noteController,
                        maxLines: 4,
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.all(16),
                          hintText: 'e.g. Something came up at work, can we do next week instead?',
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline, size: 16, color: AppColors.infoBoxText),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Cancelling within 24 hours may count toward your monthly session limit, per your plan\'s policy.',
                              style: TextStyle(fontSize: 12, color: AppColors.infoBoxText, height: 1.4),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: const Text('Keep session', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: PrimaryButton(
                        label: 'Cancel session',
                        icon: null,
                        loading: _saving,
                        onPressed: () async {
                          setState(() => _saving = true);
                          await context.read<TherapyProvider>().cancelSession(_noteController.text.trim());
                          if (!mounted) return;
                          setState(() => _saving = false);
                          Navigator.of(context).pop();
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Session cancelled. Your therapist has been notified.')),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}