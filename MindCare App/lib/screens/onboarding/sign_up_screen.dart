import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../main.dart';
import '../../providers/onboarding_provider.dart';
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
  final _phoneController = TextEditingController();
  final _cnicController = TextEditingController();

  DateTime? _dob;
  String _gender = 'Woman';
  File? _photo;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _cnicController.dispose();
    super.dispose();
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

  Future<void> _pickDob() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 25),
      firstDate: DateTime(now.year - 100),
      lastDate: now,
    );
    if (picked != null) setState(() => _dob = picked);
  }

  String _formatDob(DateTime date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return '${date.day.toString().padLeft(2, '0')} · ${months[date.month - 1]} · ${date.year}';
  }

  void _onContinue() {
    final isValid = _formKey.currentState!.validate();
    if (_dob == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select your date of birth')),
      );
      return;
    }
    if (!isValid) return;

    final provider = context.read<OnboardingProvider>();
    provider.setFullName(_nameController.text.trim());
    provider.setDateOfBirth(_dob!);
    provider.setGender(_gender);
    provider.setEmail(_emailController.text.trim());
    provider.setPhone(_phoneController.text.trim());
    provider.setCnic(_cnicController.text.trim());

    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const MobileFrame(child: FeelingCheckinScreen())),
    );
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
                            child: _photo == null
                                ? const Text('L', style: TextStyle(color: Colors.white, fontSize: 24))
                                : null,
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
                  decoration: const InputDecoration(hintText: 'Your full name'),
                ),
                const SizedBox(height: 18),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('DATE OF BIRTH', style: AppTextStyles.label()),
                          const SizedBox(height: 8),
                          GestureDetector(
                            onTap: _pickDob,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
                              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
                              child: Text(
                                _dob != null ? _formatDob(_dob!) : 'Select date',
                                style: TextStyle(color: _dob != null ? AppColors.textDark : AppColors.textMuted),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
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
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
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
                Text('PHONE', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  validator: Validators.phone,
                  decoration: const InputDecoration(hintText: '+92 333 4521 887', prefixText: 'PK   '),
                ),
                const SizedBox(height: 18),
                Text('CNIC', style: AppTextStyles.label()),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _cnicController,
                  keyboardType: TextInputType.number,
                  validator: Validators.cnic,
                  maxLength: 15,
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[0-9-]')),
                  ],
                  decoration: const InputDecoration(
                    hintText: '12345-1234567-1',
                    counterText: '',
                  ),
                ),
                const SizedBox(height: 6),
                Text('For verification only — never shown publicly.', style: AppTextStyles.body(size: 12)),
                const SizedBox(height: 26),
                Row(
                  children: [
                    Expanded(child: PrimaryButton(label: 'Continue', onPressed: _onContinue)),
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