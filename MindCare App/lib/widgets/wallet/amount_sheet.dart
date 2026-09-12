import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../common/primary_button.dart';

/// Shows a bottom sheet for entering an amount (top up or withdraw).
/// Returns the chosen amount, or null if dismissed.
Future<int?> showAmountSheet(
  BuildContext context, {
  required String title,
  required String actionLabel,
  int? maxAmount,
}) {
  return showModalBottomSheet<int>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.background,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _AmountSheetContent(title: title, actionLabel: actionLabel, maxAmount: maxAmount),
    ),
  );
}

class _AmountSheetContent extends StatefulWidget {
  const _AmountSheetContent({required this.title, required this.actionLabel, this.maxAmount});
  final String title;
  final String actionLabel;
  final int? maxAmount;

  @override
  State<_AmountSheetContent> createState() => _AmountSheetContentState();
}

class _AmountSheetContentState extends State<_AmountSheetContent> {
  final _controller = TextEditingController();
  static const _quickAmounts = [500, 1000, 5000, 10000];
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final amount = int.tryParse(_controller.text.trim());
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter a valid amount');
      return;
    }
    if (widget.maxAmount != null && amount > widget.maxAmount!) {
      setState(() => _error = 'Amount exceeds your balance (Rs ${widget.maxAmount})');
      return;
    }
    Navigator.of(context).pop(amount);
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 18), decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2))),
            ),
            Text(widget.title, style: AppTextStyles.heading(size: 22)),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
              child: TextField(
                controller: _controller,
                keyboardType: TextInputType.number,
                onChanged: (_) => setState(() => _error = null),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                  prefixText: 'Rs ',
                  hintText: '0',
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 6),
              Text(_error!, style: const TextStyle(color: AppColors.sos, fontSize: 12)),
            ],
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _quickAmounts.map((amount) {
                return GestureDetector(
                  onTap: () => setState(() {
                    _controller.text = '$amount';
                    _error = null;
                  }),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(color: AppColors.chipUnselected, borderRadius: BorderRadius.circular(20)),
                    child: Text('Rs $amount', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.chipTextUnselected)),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 22),
            PrimaryButton(label: widget.actionLabel, icon: null, onPressed: _submit),
          ],
        ),
      ),
    );
  }
}