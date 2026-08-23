class Validators {
  Validators._();

  static final RegExp _emailRegex = RegExp(
    r'^[a-zA-Z0-9.!#$%&*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$',
  );

  static final RegExp _cnicRegex = RegExp(r'^\d{5}-\d{7}-\d{1}$');

  static String? fullName(String? value) {
    if (value == null || value.trim().isEmpty) return 'Please enter your full name';
    if (value.trim().length < 2) return 'Name looks too short';
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) return 'Please enter your email';
    if (!_emailRegex.hasMatch(value.trim())) return 'Enter a valid email address';
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) return 'Please enter your phone number';
    final digitsOnly = value.replaceAll(RegExp(r'\D'), '');
    if (digitsOnly.length < 9 || digitsOnly.length > 11) return 'Enter a valid phone number';
    return null;
  }

  static String? cnic(String? value) {
    if (value == null || value.trim().isEmpty) return 'Please enter your CNIC';
    if (!_cnicRegex.hasMatch(value.trim())) return 'Format: 12345-1234567-1';
    return null;
  }

  /// Industry-standard password strength rule — min 8 chars, upper,
  /// lower, digit, and symbol. Use this wherever a password field
  /// is added later (e.g. a dedicated "set password" step).
  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Please enter a password';
    if (value.length < 8) return 'Use at least 8 characters';
    if (!RegExp(r'[A-Z]').hasMatch(value)) return 'Add at least one uppercase letter';
    if (!RegExp(r'[a-z]').hasMatch(value)) return 'Add at least one lowercase letter';
    if (!RegExp(r'\d').hasMatch(value)) return 'Add at least one number';
    if (!RegExp(r'[!@#$%^&*(),.?":{}|<>_\-]').hasMatch(value)) return 'Add at least one symbol';
    return null;
  }
}