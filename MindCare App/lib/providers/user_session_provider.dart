import 'package:flutter/material.dart';
import '../core/security/secure_storage_service.dart';

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

  /// Signs the person out: clears the display name and, critically,
  /// removes the stored auth token so the next launch of the app
  /// doesn't silently resume the old session.
  ///
  /// NOTE: in production this should also call the backend to
  /// invalidate the session/refresh token server-side, not just
  /// delete it locally — otherwise a copied token would remain valid.
  Future<void> signOut() async {
    _fullName = null;
    await SecureStorageService.instance.clearAll();
    notifyListeners();
  }
}