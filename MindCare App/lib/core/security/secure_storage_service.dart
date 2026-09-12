import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Wraps flutter_secure_storage with hardened platform options.
/// - Android: values live in EncryptedSharedPreferences, backed by
///   the Android Keystore (hardware-backed on most devices).
/// - iOS: values live in the Keychain, only readable after the
///   device has been unlocked once since boot, and never included
///   in iCloud backups.
///
/// NEVER store raw passwords here (or anywhere on-device). Only
/// short-lived session/auth tokens issued by your backend after it
/// verifies credentials over HTTPS.
class SecureStorageService {
  SecureStorageService._internal();
  static final SecureStorageService instance = SecureStorageService._internal();

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
      synchronizable: false,
    ),
  );

  static const _keyAuthToken = 'auth_token';
  static const _keyRefreshToken = 'refresh_token';

  Future<void> saveAuthToken(String token) => _storage.write(key: _keyAuthToken, value: token);
  Future<String?> getAuthToken() => _storage.read(key: _keyAuthToken);

  Future<void> saveRefreshToken(String token) => _storage.write(key: _keyRefreshToken, value: token);
  Future<String?> getRefreshToken() => _storage.read(key: _keyRefreshToken);

  Future<void> clearAll() => _storage.deleteAll();
}