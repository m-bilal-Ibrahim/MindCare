import 'package:flutter/material.dart';

import '../core/services/api_client.dart';
import '../core/services/profile_api.dart';
import '../models/profile_data.dart';
import 'motivation_provider.dart' show Loadable;

/// The signed-in patient's profile (patients/me), photo, privacy switch and
/// mental health history, plus the dropdown lists the forms need.
class ProfileProvider extends ChangeNotifier {
  ProfileProvider([ProfileApi? api]) : _api = api ?? ProfileApi();

  final ProfileApi _api;

  Loadable<PatientProfile> profile = const Loadable();

  /// Called with the patient's real name whenever the profile loads, so the
  /// greeting and avatar match the account.
  void Function(String fullName)? onName;

  Future<void> load() async {
    profile = Loadable(data: profile.data, loading: true);
    notifyListeners();
    try {
      final p = await _api.me();
      profile = Loadable(data: p);
      if (p.fullName.isNotEmpty) onName?.call(p.fullName);
    } on ApiException catch (e) {
      profile = Loadable(data: profile.data, error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  /// Loads once; later visits reuse it.
  void ensureLoaded() {
    if (!profile.hasData && !profile.loading) load();
  }

  bool saving = false;

  /// Saves changed fields. Returns null on success, or the error (with the
  /// backend's per-field messages in [ApiException.fieldErrors]).
  Future<ApiException?> update(Map<String, dynamic> changes) => _save(() => _api.update(changes));

  Future<ApiException?> uploadPhoto(List<int> bytes, String filename) => _save(() => _api.uploadPhoto(bytes, filename));

  Future<ApiException?> removePhoto() => _save(_api.removePhoto);

  Future<ApiException?> _save(Future<PatientProfile> Function() call) async {
    saving = true;
    notifyListeners();
    try {
      profile = Loadable(data: await call());
      return null;
    } on ApiException catch (e) {
      return e;
    } finally {
      saving = false;
      notifyListeners();
    }
  }

  // ----- Mental health history -----
  Loadable<MentalHealthHistory> history = const Loadable();

  Future<void> loadHistory() async {
    history = const Loadable(loading: true);
    notifyListeners();
    try {
      history = Loadable(data: await _api.history());
    } on ApiException catch (e) {
      history = Loadable(error: e.message, sessionExpired: e.isSessionExpired);
    }
    notifyListeners();
  }

  Future<ApiException?> saveHistory(MentalHealthHistory h) async {
    saving = true;
    notifyListeners();
    try {
      history = Loadable(data: await _api.saveHistory(h));
      await load(); // "missing" changes
      return null;
    } on ApiException catch (e) {
      return e;
    } finally {
      saving = false;
      notifyListeners();
    }
  }

  Future<ApiException?> deleteHistory() async {
    saving = true;
    notifyListeners();
    try {
      await _api.deleteHistory();
      history = const Loadable(data: MentalHealthHistory(concerns: []));
      await load();
      return null;
    } on ApiException catch (e) {
      return e;
    } finally {
      saving = false;
      notifyListeners();
    }
  }

  /// "Not now" on the complete-your-profile card; lasts until sign-out.
  bool completeCardDismissed = false;

  void dismissCompleteCard() {
    completeCardDismissed = true;
    notifyListeners();
  }

  // ----- Dropdown lists (cached) -----
  List<RefItem>? _countries;
  List<RefItem>? _languages;
  List<RefItem>? _specializations;

  Future<List<RefItem>> countries() async => _countries ??= await _api.countries();
  Future<List<RefItem>> languages() async => _languages ??= await _api.languages();
  Future<List<RefItem>> specializations() async => _specializations ??= await _api.specializations();
  Future<List<City>> cities(String country, String search) => _api.cities(country, search: search);

  /// Forget everything on sign-out.
  void reset() {
    profile = const Loadable();
    history = const Loadable();
    saving = false;
    completeCardDismissed = false;
    notifyListeners();
  }
}
