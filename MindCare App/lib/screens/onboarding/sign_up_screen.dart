import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../../core/services/auth_api.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../main.dart';
import '../../providers/onboarding_provider.dart';
import '../../providers/user_session_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/common/step_progress_bar.dart';
import 'feeling_checkin_screen.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  String _gender = 'Woman';
  File? _photo;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isAdultConfirmed = false;
  bool _submitting = false;

  /// Set once the account exists, so a retry after a failed sign-in
  /// doesn't try to register the same email again.
  bool _registered = false;

  /// Field errors from the backend (keys are its field names), shown under
  /// the matching input until that input is edited.
  Map<String, String> _serverErrors = const {};

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  /// Computes 1–2 initials directly from whatever is currently typed
  /// in the Full Name field — deliberately NOT read from
  /// UserSessionProvider here, since that only updates once the
  /// person taps Continue. Using it before then would show stale
  /// (empty) initials even after the person has typed their name.
  String _initialsFromTypedName() {
    final trimmed = _nameController.text.trim();
    if (trimmed.isEmpty) return '';
    final parts = trimmed.split(RegExp(r'\s+'));
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts.first.substring(0, 1) + parts.last.substring(0, 1)).toUpperCase();
  }

  Future<void> _pickPhoto() async {
    try {
      final picker = ImagePicker();
      final picked = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
      if (picked != null) {
        setState(() => _photo = File(picked.path));
        if (mounted) context.read<OnboardingProvider>().setPhoto(picked.path);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Couldn't access photos. Check app permissions in Settings.")),
        );
      }
    }
  }

  String? _validateConfirmPassword(String? value) {
    if (value == null || value.isEmpty) return 'Please confirm your password';
    if (value != _passwordController.text) return 'Passwords do not match';
    return null;
  }

  void _clearServerError(String field) {
    if (!_serverErrors.containsKey(field)) return;
    setState(() => _serverErrors = Map.of(_serverErrors)..remove(field));
  }

  /// Creates the account, signs in, then moves on to the check-in step.
  /// Date of birth is not asked here; the backend asks for it later.
  Future<void> _onContinue() async {
    if (_submitting) return;
    setState(() => _serverErrors = const {});
    if (!_formKey.currentState!.validate()) return;

    final name = _nameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    setState(() => _submitting = true);
    try {
      if (!_registered) {
        await AuthApi.instance.registerPatient(
          email: email,
          password: password,
          fullName: name,
          isAdultConfirmed: _isAdultConfirmed,
        );
        _registered = true;
      }
      await AuthApi.instance.login(email: email, password: password);
    } on AuthException catch (e) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _serverErrors = e.fieldErrors;
      });
      // Errors without a visible field (e.g. profile.timezone) go in a toast.
      const shown = {'full_name', 'email', 'password', 'is_adult_confirmed'};
      final hidden = e.fieldErrors.entries.where((f) => !shown.contains(f.key));
      final text = hidden.isNotEmpty ? hidden.first.value : (e.fieldErrors.isEmpty ? e.message : null);
      if (text != null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
      }
      return;
    }
    if (!mounted) return;

    final provider = context.read<OnboardingProvider>();
    provider.setFullName(name);
    provider.setGender(_gender);
    provider.setEmail(email);
    context.read<UserSessionProvider>().setName(name);

    // The password has done its job; don't keep it around in the form.
    _passwordController.clear();
    _confirmPasswordController.clear();
    setState(() => _submitting = false);

    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const MobileFrame(child: FeelingCheckinScreen())),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasName = _nameController.text.trim().isNotEmpty;
    final typedInitials = _initialsFromTypedName();

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
                const SizedBox(height: 4),
                const StepProgressBar(currentStep: 1, totalSteps: 3),
                const SizedBox(height: 28),
                Text.rich(
                  TextSpan(
                    style: AppTextStyles.heading(size: 30),
                    children: [
                      const TextSpan(text: "Let's get to "),
                      TextSpan(text: 'know you.', style: AppTextStyles.heading(size: 30, style: FontStyle.italic)),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Text('A few basics. You choose what your therapist sees later.', style: AppTextStyles.body()),
                const SizedBox(height: 24),
                Row(
                  children: [
                    GestureDetector(
                      onTap: _pickPhoto,
                      child: Stack(
                        children: [
                          CircleAvatar(
                            radius: 34,
                            backgroundColor: const Color(0xFFDA9A8A),
                            backgroundImage: _photo != null ? FileImage(_photo!) : null,
                            child: _photo != null
                                ? null
                                : hasName
                                    ? Text(typedInitials, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w600))
                                    : const Icon(Icons.person, color: Colors.white, size: 34),
                          ),
                          Positioned(
                            bottom: 0,
                            right: 0,
                            child: Container(
                              padding: const EdgeInsets.all(6),
                              decoration: const BoxDecoration(color: AppColors.textDark, shape: BoxShape.circle),
                              child: const Icon(Icons.camera_alt, color: Colors.white, size: 14),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Add a photo', style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark)),
                          const SizedBox(height: 2),
                          Text('Optional. Only your therapist will see this.', style: AppTextStyles.body(size: 13)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 22),
                Text('FULL NAME', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _nameController,
                  textCapitalization: TextCapitalization.words,
                  validator: Validators.fullName,
                  forceErrorText: _serverErrors['full_name'],
                  onChanged: (_) {
                    _clearServerError('full_name');
                    setState(() {});
                  },
                  decoration: const InputDecoration(hintText: 'Your full name'),
                ),
                const SizedBox(height: 18),
                Text('GENDER', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: _gender,
                      isExpanded: true,
                      items: const ['Woman', 'Man', 'Non-binary', 'Prefer not to say']
                          .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                          .toList(),
                      onChanged: (value) => setState(() => _gender = value ?? _gender),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                Text('EMAIL', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  autocorrect: false,
                  validator: Validators.email,
                  forceErrorText: _serverErrors['email'],
                  onChanged: (_) {
                    _clearServerError('email');
                    // A different email means a different account to create.
                    _registered = false;
                  },
                  decoration: const InputDecoration(hintText: 'you@example.com'),
                ),
                const SizedBox(height: 22),
                Text('PASSWORD', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  validator: Validators.password,
                  forceErrorText: _serverErrors['password'],
                  onChanged: (_) => _clearServerError('password'),
                  decoration: InputDecoration(
                    hintText: 'Create a password',
                    suffixIcon: IconButton(
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      icon: Icon(_obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textMuted),
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text('At least 8 characters, with upper, lower, a number, and a symbol.', style: AppTextStyles.body(size: 12)),
                const SizedBox(height: 18),
                Text('CONFIRM PASSWORD', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _confirmPasswordController,
                  obscureText: _obscureConfirmPassword,
                  validator: _validateConfirmPassword,
                  decoration: InputDecoration(
                    hintText: 'Re-enter your password',
                    suffixIcon: IconButton(
                      onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                      icon: Icon(_obscureConfirmPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textMuted),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                FormField<bool>(
                  initialValue: _isAdultConfirmed,
                  forceErrorText: _serverErrors['is_adult_confirmed'],
                  validator: (_) => _isAdultConfirmed ? null : 'Please confirm you are 18 or older',
                  builder: (field) => Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () {
                          setState(() => _isAdultConfirmed = !_isAdultConfirmed);
                          field.didChange(_isAdultConfirmed);
                          _clearServerError('is_adult_confirmed');
                        },
                        child: Row(
                          children: [
                            Checkbox(
                              value: _isAdultConfirmed,
                              activeColor: AppColors.primaryDark,
                              onChanged: (value) {
                                setState(() => _isAdultConfirmed = value ?? false);
                                field.didChange(_isAdultConfirmed);
                                _clearServerError('is_adult_confirmed');
                              },
                            ),
                            Expanded(
                              child: Text(
                                'I confirm I am 18 or older',
                                style: AppTextStyles.body(size: 15, color: AppColors.textDark),
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (field.hasError)
                        Padding(
                          padding: const EdgeInsets.only(left: 12, top: 2),
                          child: Text(
                            field.errorText!,
                            style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                Row(
                  children: [
                    Expanded(
                      child: PrimaryButton(
                        label: 'Continue',
                        loading: _submitting,
                        onPressed: _onContinue,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const SosButton(),
                  ],
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