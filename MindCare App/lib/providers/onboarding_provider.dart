import 'package:flutter/material.dart';
import '../models/onboarding_data.dart';

class OnboardingProvider extends ChangeNotifier {
  final OnboardingData data = OnboardingData();

  void setPhoto(String? path) {
    data.photoPath = path;
    notifyListeners();
  }

  void setFullName(String value) => data.fullName = value;

  void setDateOfBirth(DateTime date) {
    data.dateOfBirth = date;
    notifyListeners();
  }

  void setGender(String value) {
    data.gender = value;
    notifyListeners();
  }

  void setEmail(String value) => data.email = value;
  void setPhone(String value) => data.phone = value;
  void setCnic(String value) => data.cnic = value;
  void setPassword(String value) => data.password = value;

  void toggleMood(String mood) {
    if (data.selectedMoods.contains(mood)) {
      data.selectedMoods.remove(mood);
    } else {
      data.selectedMoods.add(mood);
    }
    notifyListeners();
  }

  void setIntensity(double value) {
    data.intensity = value;
    notifyListeners();
  }

  void setTherapistHistory(String value) {
    data.therapistHistory = value;
    notifyListeners();
  }

  void setOnMedication(bool value) {
    data.onMedication = value;
    notifyListeners();
  }

  void toggleConcern(String concern) {
    if (data.concerns.contains(concern)) {
      data.concerns.remove(concern);
    } else {
      data.concerns.add(concern);
    }
    notifyListeners();
  }

  /// Called once the whole onboarding flow finishes.
  ///
  /// NOTE: demo/placeholder only. In production this sends `data`
  /// (including the plaintext password, only over HTTPS) to a
  /// backend endpoint that hashes it immediately with bcrypt/argon2
  /// and stores only the hash — the plaintext password must never be
  /// written to any database, log, or file, on the client or server.
  /// The backend then returns a session token, which is the ONLY
  /// thing saved on-device, via SecureStorageService.
  Future<void> finishSetup() async {
    // TODO: replace with a real API call, e.g.:
    // final token = await AuthApi.completeOnboarding(data);
    // await SecureStorageService.instance.saveAuthToken(token);
    await Future.delayed(const Duration(milliseconds: 600));
    debugPrint('Submitting onboarding: ${data.toRedactedMap()}');

    // Clear the password from memory now that "submission" is done —
    // it has no further reason to exist in this session's state.
    data.password = '';
  }
}