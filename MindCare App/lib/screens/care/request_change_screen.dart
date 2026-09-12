import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../widgets/common/primary_button.dart';

class RequestChangeScreen extends StatefulWidget {
  const RequestChangeScreen({super.key});

  @override
  State<RequestChangeScreen> createState() => _RequestChangeScreenState();
}

class _RequestChangeScreenState extends State<RequestChangeScreen> {
  static const _reasons = [
    'Too much this week',
    'Not enough / want more',
    'A task doesn\'t feel right',
    'Something else',
  ];

  String _selectedReason = _reasons.first;
  final _noteController = TextEditingController();
  bool _sending = false;
  bool _sent = false;

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_sent) {
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
                Text('Sent to Dr. Tariq.', style: AppTextStyles.heading(size: 24)),
                const SizedBox(height: 8),
                Text(
                  'He usually reviews program change requests within a day or two, and any update will show up right here.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.body(),
                ),
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
                          'REQUEST A CHANGE',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('What would you like to change?', style: AppTextStyles.heading(size: 22)),
                  const SizedBox(height: 8),
                  Text(
                    'Your program stays set by Dr. Tariq, but he wants your input. This goes straight to him, not Aida.',
                    style: AppTextStyles.body(),
                  ),
                  const SizedBox(height: 22),
                  Text('REASON', style: AppTextStyles.label()),
                  const SizedBox(height: 10),
                  ..._reasons.map((reason) {
                    final selected = _selectedReason == reason;
                    return GestureDetector(
                      onTap: () => setState(() => _selectedReason = reason),
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: selected ? AppColors.textDark : Colors.transparent, width: 1.6),
                        ),
                        child: Row(
                          children: [
                            Expanded(child: Text(reason, style: const TextStyle(fontSize: 14, color: AppColors.textDark, fontWeight: FontWeight.w500))),
                            Container(
                              width: 20,
                              height: 20,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: selected ? AppColors.textDark : Colors.transparent,
                                border: selected ? null : Border.all(color: AppColors.border, width: 1.5),
                              ),
                              child: selected ? const Icon(Icons.check, size: 13, color: Colors.white) : null,
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                  const SizedBox(height: 16),
                  Text('TELL DR. TARIQ MORE (OPTIONAL)', style: AppTextStyles.label()),
                  const SizedBox(height: 10),
                  Container(
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                    child: TextField(
                      controller: _noteController,
                      maxLines: 4,
                      maxLength: 300,
                      decoration: const InputDecoration(
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.all(16),
                        hintText: 'e.g. The evening journal is hard to fit in before bed lately.',
                        counterText: '',
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
              child: PrimaryButton(
                label: 'Send request',
                icon: null,
                loading: _sending,
                onPressed: () async {
                  setState(() => _sending = true);
                  await Future.delayed(const Duration(milliseconds: 600));
                  if (!mounted) return;
                  setState(() {
                    _sending = false;
                    _sent = true;
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