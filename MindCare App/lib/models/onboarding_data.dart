class OnboardingData {
  String? photoPath;
  String fullName;
  DateTime? dateOfBirth;
  String gender;
  String email;
  String phone;
  String cnic;

  /// Held only in memory for the duration of the sign-up flow, long
  /// enough to send once over HTTPS to the backend for hashing
  /// (bcrypt/argon2) and storage. Never written to disk, never logged,
  /// and cleared immediately after the account-creation request
  /// completes via clearPassword().
  String password;

  Set<String> selectedMoods;
  double intensity;

  String therapistHistory;
  bool onMedication;
  Set<String> concerns;

  OnboardingData({
    this.photoPath,
    this.fullName = '',
    this.dateOfBirth,
    this.gender = 'Woman',
    this.email = '',
    this.phone = '',
    this.cnic = '',
    this.password = '',
    Set<String>? selectedMoods,
    this.intensity = 0.5,
    this.therapistHistory = 'Never',
    this.onMedication = false,
    Set<String>? concerns,
  })  : selectedMoods = selectedMoods ?? <String>{},
        concerns = concerns ?? <String>{};

  /// Redacts sensitive fields (CNIC, phone, email, password) so PII
  /// never ends up in debug logs or crash reports.
  Map<String, dynamic> toRedactedMap() {
    return {
      'fullName': fullName,
      'email': _maskEmail(email),
      'phone': '***redacted***',
      'cnic': '***redacted***',
      'password': '***redacted***',
      'gender': gender,
      'selectedMoods': selectedMoods.toList(),
      'intensity': intensity,
    };
  }

  String _maskEmail(String value) {
    final at = value.indexOf('@');
    if (at <= 1) return '***';
    return '${value.substring(0, 1)}***${value.substring(at)}';
  }
}