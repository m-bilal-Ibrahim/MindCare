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
  /// In production this sends `data` to your backend over HTTPS
  /// (never plain HTTP), the backend hashes/stores it securely
  /// (e.g. bcrypt/argon2 for any password, encrypted-at-rest DB
  /// columns for CNIC), and returns a session token — which is the
  /// ONLY thing saved on-device, via SecureStorageService.
  Future<void> finishSetup() async {
    // TODO: replace with a real API call, e.g.:
    // final token = await AuthApi.completeOnboarding(data);
    // await SecureStorageService.instance.saveAuthToken(token);
    await Future.delayed(const Duration(milliseconds: 600));
    debugPrint('Submitting onboarding: ${data.toRedactedMap()}');
  }
}
