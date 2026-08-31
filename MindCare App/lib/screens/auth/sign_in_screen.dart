import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/security/secure_storage_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../main.dart';
import '../../providers/user_session_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';
import 'forgot_password_screen.dart';

class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends State<SignInScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _loading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _onSignIn() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    await Future.delayed(const Duration(milliseconds: 800));
    await SecureStorageService.instance.saveAuthToken('demo-session-token');

    if (!mounted) return;

    context.read<UserSessionProvider>().setNameFromEmailIfUnset(_emailController.text.trim());

    setState(() => _loading = false);
    Navigator.of(context).pushNamedAndRemoveUntil('/home', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
                Text.rich(
                  TextSpan(
                    style: AppTextStyles.heading(size: 32),
                    children: [
                      const TextSpan(text: 'Welcome\n'),
                      TextSpan(text: 'back.', style: AppTextStyles.heading(size: 32, style: FontStyle.italic)),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Text('Sign in to pick up right where you left off.', style: AppTextStyles.body()),
                const SizedBox(height: 32),
                Text('EMAIL', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  autocorrect: false,
                  validator: Validators.email,
                  decoration: const InputDecoration(hintText: 'you@example.com'),
                ),
                const SizedBox(height: 18),
                Text('PASSWORD', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  validator: (value) => (value == null || value.isEmpty) ? 'Please enter your password' : null,
                  decoration: InputDecoration(
                    hintText: 'Your password',
                    suffixIcon: IconButton(
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      icon: Icon(_obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textMuted),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const MobileFrame(child: ForgotPasswordScreen())),
                    ),
                    child: const Text('Forgot password?', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600, fontSize: 13)),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(child: PrimaryButton(label: 'Sign in', icon: null, loading: _loading, onPressed: _onSignIn)),
                    const SizedBox(width: 12),
                    const SosButton(),
                  ],
                ),
                const SizedBox(height: 24),
                Center(
                  child: TextButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    child: RichText(
                      text: const TextSpan(
                        style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                        children: [
                          TextSpan(text: "New here? "),
                          TextSpan(text: 'Create an account', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }
}