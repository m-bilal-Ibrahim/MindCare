import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../widgets/common/primary_button.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _sending = false;
  bool _sent = false;

  @override
  void dispose() {
    _emailController.dispose();
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
                  child: const Icon(Icons.mail_outline, color: Colors.white, size: 36),
                ),
                const SizedBox(height: 24),
                Text('Check your inbox.', style: AppTextStyles.heading(size: 24)),
                const SizedBox(height: 8),
                Text(
                  "If an account exists for ${_emailController.text.trim()}, we've sent a link to reset your password.",
                  textAlign: TextAlign.center,
                  style: AppTextStyles.body(),
                ),
                const SizedBox(height: 32),
                PrimaryButton(label: 'Back to sign in', icon: null, onPressed: () => Navigator.of(context).pop()),
              ],
            ),
          ),
        ),
      );
    }

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
                IconButton(
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.arrow_back, color: AppColors.textDark),
                  padding: EdgeInsets.zero,
                  alignment: Alignment.centerLeft,
                ),
                const SizedBox(height: 24),
                Text('Reset your password.', style: AppTextStyles.heading(size: 28)),
                const SizedBox(height: 10),
                Text("Enter your email and we'll send you a link to reset it.", style: AppTextStyles.body()),
                const SizedBox(height: 28),
                Text('EMAIL', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  autocorrect: false,
                  validator: Validators.email,
                  decoration: const InputDecoration(hintText: 'you@example.com'),
                ),
                const SizedBox(height: 28),
                PrimaryButton(
                  label: 'Send reset link',
                  icon: null,
                  loading: _sending,
                  onPressed: () async {
                    if (!_formKey.currentState!.validate()) return;
                    setState(() => _sending = true);
                    // NOTE: demo/placeholder only. A real implementation
                    // sends this over HTTPS to a backend endpoint that
                    // issues a short-lived, single-use reset token via
                    // email — never resets a password directly from
                    // client-side input.
                    await Future.delayed(const Duration(milliseconds: 600));
                    if (!mounted) return;
                    setState(() {
                      _sending = false;
                      _sent = true;
                    });
                  },
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}