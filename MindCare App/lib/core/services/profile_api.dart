import '../../models/profile_data.dart';
import 'api_client.dart';

/// Patient profile endpoints (backend handoff: user-onboarding-profile.md).
class ProfileApi {
  ProfileApi([ApiClient? client]) : _api = client ?? ApiClient.instance;

  final ApiClient _api;

  Future<PatientProfile> me() async => PatientProfile.fromJson(await _api.get('/patients/me/') as Map<String, dynamic>);

  /// Sends only the fields that changed. Keys: country (code), city (name),
  /// date_of_birth (yyyy-mm-dd), gender, phone_number, preferred_language
  /// (code), is_profile_public.
  Future<PatientProfile> update(Map<String, dynamic> changes) async =>
      PatientProfile.fromJson(await _api.patch('/patients/me/', changes) as Map<String, dynamic>);

  Future<PatientProfile> uploadPhoto(List<int> bytes, String filename) async =>
      PatientProfile.fromJson(await _api.putFile('/patients/me/photo/', field: 'photo', bytes: bytes, filename: filename) as Map<String, dynamic>);

  Future<PatientProfile> removePhoto() async => PatientProfile.fromJson(await _api.delete('/patients/me/photo/') as Map<String, dynamic>);

  Future<MentalHealthHistory> history() async => MentalHealthHistory.fromJson(await _api.get('/patients/me/history/') as Map<String, dynamic>);

  Future<MentalHealthHistory> saveHistory(MentalHealthHistory h) async =>
      MentalHealthHistory.fromJson(await _api.put('/patients/me/history/', h.toJson()) as Map<String, dynamic>);

  Future<void> deleteHistory() => _api.delete('/patients/me/history/');

  Future<List<RefItem>> countries() async =>
      (await _api.get('/reference/countries/') as List).whereType<Map<String, dynamic>>().map(RefItem.country).toList();

  Future<List<RefItem>> languages() async =>
      (await _api.get('/reference/languages/') as List).whereType<Map<String, dynamic>>().map(RefItem.language).toList();

  Future<List<RefItem>> specializations() async =>
      (await _api.get('/reference/specializations/') as List).whereType<Map<String, dynamic>>().map(RefItem.specialization).toList();

  /// Up to 20 matching cities in a country.
  Future<List<City>> cities(String countryCode, {String search = ''}) async {
    final body = await _api.get('/reference/cities/', query: {'country': countryCode, if (search.isNotEmpty) 'search': search});
    return (body as List).whereType<Map<String, dynamic>>().map(City.fromJson).toList();
  }
}
