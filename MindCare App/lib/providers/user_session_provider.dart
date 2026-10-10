import 'package:flutter/material.dart';
import '../core/security/secure_storage_service.dart';
import '../core/services/auth_api.dart';

/// Holds the signed-in person's identity for display across the app —
/// greeting text, avatar initials, and the Profile header.
class UserSessionProvider extends ChangeNotifier {
  String? _fullName;

  String? get fullName => _fullName;
  bool get isSignedIn => _fullName != null;

  String get firstName {
    if (_fullName == null || _fullName!.trim().isEmpty) return 'there';
    return _fullName!.trim().split(' ').first;
  }

  String get initials {
    if (_fullName == null || _fullName!.trim().isEmpty) return '?';
    final parts = _fullName!.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts.first.substring(0, 1) + parts.last.substring(0, 1)).toUpperCase();
  }

  void setName(String name) {
    final trimmed = name.trim();
    if (trimmed.isEmpty) return;
    _fullName = trimmed;
    notifyListeners();
  }

  void setNameFromEmailIfUnset(String email) {
    if (_fullName != null && _fullName!.trim().isNotEmpty) return;
    final localPart = email.split('@').first;
    final words = localPart.split(RegExp(r'[._\-]+')).where((w) => w.isNotEmpty);
    final capitalized = words.map((w) => w[0].toUpperCase() + w.substring(1)).join(' ');
    if (capitalized.isNotEmpty) {
      _fullName = capitalized;
      notifyListeners();
    }
  }

  /// Signs the person out: asks the backend to blacklist the refresh
  /// token (so a copied token stops working), then clears the display
  /// name and the stored tokens so the next launch doesn't silently
  /// resume the old session.
  Future<void> signOut() async {
    _fullName = null;
    await AuthApi.instance.logout();
    await SecureStorageService.instance.clearAll();
    notifyListeners();
  }
}