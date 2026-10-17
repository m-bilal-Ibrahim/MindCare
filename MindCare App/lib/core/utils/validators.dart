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

  // ----- Rules shared with the backend (MindCare Backend/docs/validation-rules.md) -----
  // Same order and same messages as the backend, so a field shows one message
  // at a time and the app never accepts what the server will reject.

  static final RegExp _controlChars = RegExp(r'[\u0000-\u001F\u007F]');

  /// Single-line normalisation: control characters removed, trimmed, runs of
  /// spaces collapsed.
  static String normalizeLine(String value) => value.replaceAll(_controlChars, '').trim().replaceAll(RegExp(r'\s+'), ' ');

  /// Multi-line normalisation: CRLF to LF, a tab becomes a space, other control
  /// characters except newline removed, spaces collapsed within each line.
  static String normalizeMultiline(String value) {
    final text = value.replaceAll('\r\n', '\n').replaceAll('\t', ' ').replaceAll(RegExp(r'[\u0000-\u0009\u000B-\u001F\u007F]'), '');
    return text.split('\n').map((l) => l.replaceAll(RegExp(r' +'), ' ').trim()).join('\n').trim();
  }

  static final RegExp _letter = RegExp(r'\p{L}', unicode: true);
  static final RegExp _personNameChars = RegExp(r"^[\p{L}\p{M} \-'’.]+$", unicode: true);

  /// Person name (full name, city, quote author). Empty passes; check
  /// required-ness separately.
  static String? personName(String? value, {required String label}) {
    final v = normalizeLine(value ?? '');
    if (v.isEmpty) return null;
    if (!_personNameChars.hasMatch(v)) return "$label can only contain letters, spaces, hyphens (-), apostrophes (') and dots (.).";
    if (v.length < 2 || v.length > 100) return '$label must be between 2 and 100 characters.';
    if (_letter.allMatches(v).length < 2) return '$label must contain at least 2 letters.';
    return null;
  }

  /// Phone normalisation: spaces, dashes, dots and brackets removed; a leading
  /// 00 becomes +; a Pakistani local number (single leading 0 then 9–10
  /// digits) becomes +92… without the 0.
  static String normalizePhone(String value) {
    var p = normalizeLine(value).replaceAll(RegExp(r'[\s\-.()]'), '');
    if (p.startsWith('00')) p = '+${p.substring(2)}';
    if (RegExp(r'^0\d{9,10}$').hasMatch(p)) p = '+92${p.substring(1)}';
    return p;
  }

  static const String phoneMessage =
      'Enter a phone number in international format (e.g. +923001234567), or a Pakistani number starting with 0 (e.g. 03001234567).';

  /// Optional phone number. Empty passes.
  static String? phoneNumber(String? value) {
    if (normalizeLine(value ?? '').isEmpty) return null;
    if (!RegExp(r'^\+[1-9]\d{6,14}$').hasMatch(normalizePhone(value!))) return phoneMessage;
    return null;
  }

  /// Date of birth: not in the future, 18 or over, 120 or under. Null passes.
  static String? dateOfBirth(DateTime? value, {DateTime? today}) {
    if (value == null) return null;
    final now = today ?? DateTime.now();
    final day = DateTime(now.year, now.month, now.day);
    final dob = DateTime(value.year, value.month, value.day);
    if (dob.isAfter(day)) return "Date of birth can't be in the future.";
    var age = day.year - dob.year;
    if (day.month < dob.month || (day.month == dob.month && day.day < dob.day)) age--;
    if (age < 18) return 'You must be 18 or older to use MindCare.';
    if (age > 120) return 'Enter a real date of birth (age 120 or under).';
    return null;
  }

  /// Free text (notes, bios, descriptions). Optional fields may be empty.
  static String? freeText(String? value, {required String label, required int min, required int max, bool optional = true}) {
    final v = normalizeMultiline(value ?? '');
    if (v.isEmpty) return optional ? null : '$label must be between $min and $max characters.';
    if (v.length < min || v.length > max) return '$label must be between $min and $max characters.';
    if (RegExp(r'<[A-Za-z/!?]').hasMatch(v)) return "$label can't contain HTML tags.";
    if (_letter.allMatches(v).length < 3) return '$label must contain at least 3 letters.';
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