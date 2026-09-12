import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/primary_button.dart';

class AddPaymentMethodScreen extends StatefulWidget {
  const AddPaymentMethodScreen({super.key});

  @override
  State<AddPaymentMethodScreen> createState() => _AddPaymentMethodScreenState();
}

class _AddPaymentMethodScreenState extends State<AddPaymentMethodScreen> {
  final _formKey = GlobalKey<FormState>();
  final _cardNumberController = TextEditingController();
  final _expiryController = TextEditingController();
  final _cvvController = TextEditingController();
  final _nameController = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _cardNumberController.dispose();
    _expiryController.dispose();
    _cvvController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  String? _validateCardNumber(String? value) {
    if (value == null || value.trim().isEmpty) return 'Enter your card number';
    final digitsOnly = value.replaceAll(' ', '');
    if (digitsOnly.length < 13 || digitsOnly.length > 19 || !RegExp(r'^\d+$').hasMatch(digitsOnly)) {
      return 'Enter a valid card number';
    }
    return null;
  }

  String? _validateExpiry(String? value) {
    if (value == null || !RegExp(r'^\d{2}\s?/\s?\d{2}$').hasMatch(value)) return 'MM / YY';
    return null;
  }

  String? _validateCvv(String? value) {
    if (value == null || !RegExp(r'^\d{3,4}$').hasMatch(value)) return '3-4 digits';
    return null;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _saving = true);
    await Future.delayed(const Duration(milliseconds: 500));

    final digitsOnly = _cardNumberController.text.replaceAll(' ', '');
    final lastFour = digitsOnly.substring(digitsOnly.length - 4);
    final cardBrand = digitsOnly.startsWith('4') ? 'Visa' : digitsOnly.startsWith('5') ? 'Mastercard' : 'Card';

    context.read<AccountProvider>().addPaymentMethod(
          name: cardBrand,
          lastFour: lastFour,
          expiry: _expiryController.text.replaceAll(' ', ''),
        );

    if (!mounted) return;
    setState(() => _saving = false);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Form(
            key: _formKey,
            autovalidateMode: AutovalidateMode.onUserInteraction,
            child: ListView(
              children: [
                const SizedBox(height: 8),
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.close, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'ADD CARD',
                        textAlign: TextAlign.center,
                        style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                      ),
                    ),
                    const SizedBox(width: 48),
                  ],
                ),
                const SizedBox(height: 8),
                Text('New payment method.', style: AppTextStyles.heading(size: 26)),
                const SizedBox(height: 22),
                Text('CARD NUMBER', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _cardNumberController,
                  keyboardType: TextInputType.number,
                  validator: _validateCardNumber,
                  decoration: const InputDecoration(hintText: '1234 5678 9012 3456'),
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('EXPIRY', style: AppTextStyles.label()),
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _expiryController,
                            keyboardType: TextInputType.number,
                            validator: _validateExpiry,
                            decoration: const InputDecoration(hintText: 'MM / YY'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('CVV', style: AppTextStyles.label()),
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _cvvController,
                            keyboardType: TextInputType.number,
                            obscureText: true,
                            validator: _validateCvv,
                            decoration: const InputDecoration(hintText: '123'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Text('NAME ON CARD', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _nameController,
                  textCapitalization: TextCapitalization.words,
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter the name on your card' : null,
                  decoration: const InputDecoration(hintText: 'As shown on the card'),
                ),
                const SizedBox(height: 18),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
                  child: Row(
                    children: [
                      const Icon(Icons.lock_outline, size: 16, color: AppColors.infoBoxText),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Encrypted and processed securely. We never store your full card number.',
                          style: TextStyle(fontSize: 12, color: AppColors.infoBoxText),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 26),
                PrimaryButton(label: 'Save card', icon: null, loading: _saving, onPressed: _save),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}