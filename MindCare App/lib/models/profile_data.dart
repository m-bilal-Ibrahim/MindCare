// The patient's own profile as the backend sends it (6.1, patients/me).

class RefItem {
  const RefItem({required this.code, required this.name});

  /// Country/language code, or a specialization slug.
  final String code;
  final String name;

  factory RefItem.country(Map<String, dynamic> j) => RefItem(code: j['code'] as String, name: j['name'] as String);
  factory RefItem.language(Map<String, dynamic> j) => RefItem(code: j['code'] as String, name: j['name'] as String);
  factory RefItem.specialization(Map<String, dynamic> j) => RefItem(code: j['slug'] as String, name: j['name'] as String);

  @override
  bool operator ==(Object other) => other is RefItem && other.code == code;
  @override
  int get hashCode => code.hashCode;
}

class City {
  const City({required this.id, required this.name, required this.country});
  final int id;
  final String name;
  final String country;

  factory City.fromJson(Map<String, dynamic> j) => City(id: j['id'] as int, name: j['name'] as String, country: j['country'] as String? ?? '');
}

enum Gender {
  female('female', 'Female'),
  male('male', 'Male'),
  other('other', 'Other'),
  preferNotToSay('prefer_not_to_say', 'Prefer not to say');

  const Gender(this.api, this.label);
  final String api;
  final String label;

  static Gender? fromApi(String? v) {
    for (final g in values) {
      if (g.api == v) return g;
    }
    return null;
  }
}

/// Labels for the optional profile parts the backend lists as missing.
const Map<String, String> profilePartLabels = {
  'date_of_birth': 'Date of birth',
  'gender': 'Gender',
  'phone_number': 'Phone number',
  'city': 'City',
  'preferred_language': 'Preferred language',
  'photo': 'Profile photo',
  'mental_health_history': 'Mental health history',
};

class PatientProfile {
  const PatientProfile({
    required this.pseudonym,
    required this.fullName,
    required this.isPublic,
    required this.shownWhenPublic,
    required this.alwaysPrivate,
    required this.missing,
    this.photoUrl,
    this.country,
    this.city,
    this.timezone,
    this.dateOfBirth,
    this.gender,
    this.phoneNumber,
    this.language,
  });

  final String pseudonym;
  final String fullName;
  final bool isPublic;
  final List<String> shownWhenPublic;
  final List<String> alwaysPrivate;

  /// Optional parts not filled in yet, for "complete your profile".
  final List<String> missing;

  /// Signed link valid for a few minutes; refetch the profile for a fresh one.
  final String? photoUrl;
  final RefItem? country;
  final City? city;
  final String? timezone;
  final DateTime? dateOfBirth;
  final Gender? gender;
  final String? phoneNumber;
  final RefItem? language;

  factory PatientProfile.fromJson(Map<String, dynamic> j) {
    final privacy = j['privacy'] as Map<String, dynamic>? ?? const {};
    final completion = j['profile_completion'] as Map<String, dynamic>? ?? const {};
    List<String> strings(Object? v) => (v as List? ?? const []).map((e) => e.toString()).toList();
    final dob = j['date_of_birth'] as String?;
    return PatientProfile(
      pseudonym: j['pseudonym'] as String? ?? '',
      fullName: j['full_name'] as String? ?? '',
      isPublic: j['is_profile_public'] as bool? ?? false,
      shownWhenPublic: strings(privacy['shown_when_public']),
      alwaysPrivate: strings(privacy['always_private']),
      missing: strings(completion['missing']),
      photoUrl: j['photo_url'] as String?,
      country: j['country'] is Map<String, dynamic> ? RefItem.country(j['country'] as Map<String, dynamic>) : null,
      city: j['city'] is Map<String, dynamic> ? City.fromJson(j['city'] as Map<String, dynamic>) : null,
      timezone: j['timezone'] as String?,
      dateOfBirth: dob == null ? null : DateTime.tryParse(dob),
      gender: Gender.fromApi(j['gender'] as String?),
      phoneNumber: (j['phone_number'] as String?)?.isEmpty == true ? null : j['phone_number'] as String?,
      language: j['preferred_language'] is Map<String, dynamic> ? RefItem.language(j['preferred_language'] as Map<String, dynamic>) : null,
    );
  }
}

/// Choices for the history questions.
enum HistoryAnswer {
  yes('yes', 'Yes'),
  no('no', 'No'),
  preferNotToSay('prefer_not_to_say', 'Prefer not to say');

  const HistoryAnswer(this.api, this.label);
  final String api;
  final String label;

  static HistoryAnswer? fromApi(String? v) {
    for (final a in values) {
      if (a.api == v) return a;
    }
    return null;
  }
}

class MentalHealthHistory {
  const MentalHealthHistory({
    required this.concerns,
    this.previousDiagnosis,
    this.currentMedication,
    this.previousTherapy,
    this.notes = '',
    this.isEmpty = true,
    this.updatedAt,
  });

  final List<RefItem> concerns;
  final HistoryAnswer? previousDiagnosis;
  final HistoryAnswer? currentMedication;

  /// Yes or No only (no "prefer not to say" on this one).
  final HistoryAnswer? previousTherapy;
  final String notes;
  final bool isEmpty;
  final DateTime? updatedAt;

  factory MentalHealthHistory.fromJson(Map<String, dynamic> j) => MentalHealthHistory(
        concerns: (j['concerns'] as List? ?? const []).whereType<Map<String, dynamic>>().map(RefItem.specialization).toList(),
        previousDiagnosis: HistoryAnswer.fromApi(j['previous_diagnosis'] as String?),
        currentMedication: HistoryAnswer.fromApi(j['current_medication'] as String?),
        previousTherapy: HistoryAnswer.fromApi(j['previous_therapy'] as String?),
        notes: j['notes'] as String? ?? '',
        isEmpty: j['is_empty'] as bool? ?? true,
        updatedAt: j['updated_at'] == null ? null : DateTime.tryParse(j['updated_at'] as String),
      );

  /// The PUT body: the whole history (anything left out is cleared).
  Map<String, dynamic> toJson() => {
        'concerns': concerns.map((c) => c.code).toList(),
        'previous_diagnosis': previousDiagnosis?.api,
        'current_medication': currentMedication?.api,
        'previous_therapy': previousTherapy?.api,
        'notes': notes.isEmpty ? null : notes,
      };
}
