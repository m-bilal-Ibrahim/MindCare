import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:http/http.dart' as http;

import '../security/secure_storage_service.dart';

/// Talks to the MindCare backend's accounts API.
///
/// The base URL can be overridden at build time, e.g. for a local backend:
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
class AuthApi {
  AuthApi._({http.Client? client}) : _client = client ?? http.Client();
  static final instance = AuthApi._();

  @visibleForTesting
  AuthApi.withClient(http.Client client) : _client = client;

  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://mindcare-ajri.onrender.com/api/v1',
  );

  // Render's free tier sleeps when idle; the first request can take ~a minute.
  static const _timeout = Duration(seconds: 90);

  final http.Client _client;

  /// Creates a patient account. Returns normally on 201; the backend issues
  /// no tokens here, so call [login] next.
  ///
  /// Date of birth is deliberately not collected at signup; the backend asks
  /// for it later, before the first psychologist request.
  Future<void> registerPatient({
    required String email,
    required String password,
    required String fullName,
    required bool isAdultConfirmed,
  }) async {
    final timezone = await _deviceTimezone();
    await _post('/accounts/register/', {
      'email': email,
      'password': password,
      'full_name': fullName,
      'role': 'patient',
      // Must be the JSON boolean true; the backend rejects "true" or 1.
      'is_adult_confirmed': isAdultConfirmed,
      'profile': {'timezone': timezone},
    });
  }

  /// Signs in and stores the access/refresh tokens in secure storage.
  /// Returns the account's role from the access token.
  Future<String?> login({required String email, required String password}) async {
    final body = await _post('/accounts/login/', {
      'email': email,
      'password': password,
    });
    final access = body['access'] as String?;
    final refresh = body['refresh'] as String?;
    if (access == null || refresh == null) {
      throw const AuthException('Sign-in failed. Please try again.');
    }
    final role = _claim(access, 'role');
    if (role != null && role != 'patient') {
      // Psychologists and NGOs use the MindCare website, not this app.
      throw const AuthException(
        'This app is for people seeking care. Psychologists and NGOs can '
        'sign in on the MindCare website.',
      );
    }
    final storage = SecureStorageService.instance;
    await storage.saveAuthToken(access);
    await storage.saveRefreshToken(refresh);
    return role;
  }

  /// Best-effort server-side logout: blacklists the refresh token so a
  /// copied token stops working. Local tokens are cleared by the caller.
  Future<void> logout() async {
    final storage = SecureStorageService.instance;
    final refresh = await storage.getRefreshToken();
    final access = await storage.getAuthToken();
    if (refresh == null) return;
    try {
      await _client
          .post(
            Uri.parse('$baseUrl/accounts/logout/'),
            headers: {
              'Content-Type': 'application/json',
              if (access != null) 'Authorization': 'Bearer $access',
            },
            body: jsonEncode({'refresh': refresh}),
          )
          .timeout(const Duration(seconds: 15));
    } catch (_) {
      // Offline or already expired; signing out locally still proceeds.
    }
  }

  Future<String> _deviceTimezone() async {
    try {
      final tz = await FlutterTimezone.getLocalTimezone();
      if (tz.identifier.contains('/') || tz.identifier == 'UTC') {
        return tz.identifier;
      }
    } catch (_) {}
    return 'UTC';
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> payload) async {
    final http.Response response;
    try {
      response = await _client
          .post(
            Uri.parse('$baseUrl$path'),
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(_timeout);
    } catch (_) {
      throw const AuthException(
        "Couldn't reach MindCare's servers. Check your connection and try again.",
      );
    }

    final decoded = _decode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded is Map<String, dynamic> ? decoded : const {};
    }
    throw AuthException.fromResponse(response.statusCode, decoded);
  }

  static Object? _decode(String body) {
    if (body.isEmpty) return null;
    try {
      return jsonDecode(body);
    } catch (_) {
      return null;
    }
  }

  /// Reads a claim from a JWT's payload without verifying it (the server
  /// verifies tokens; this is only for routing on the client).
  static String? _claim(String jwt, String name) {
    final parts = jwt.split('.');
    if (parts.length != 3) return null;
    try {
      final payload = utf8.decode(base64Url.decode(base64Url.normalize(parts[1])));
      final value = (jsonDecode(payload) as Map<String, dynamic>)[name];
      return value?.toString();
    } catch (_) {
      return null;
    }
  }
}

/// A failed auth request. [fieldErrors] maps form fields to the backend's
/// messages (profile errors are flattened as `profile.<field>`); [message]
/// is what to show when an error doesn't belong to a visible field.
class AuthException implements Exception {
  const AuthException(this.message, {this.fieldErrors = const {}});

  final String message;
  final Map<String, String> fieldErrors;

  factory AuthException.fromResponse(int status, Object? body) {
    final fields = <String, String>{};
    String? general;

    void collect(Map<String, dynamic> map, String prefix) {
      map.forEach((key, value) {
        if (value is Map<String, dynamic>) {
          collect(value, '$prefix$key.');
          return;
        }
        final text = value is List
            ? value.whereType<Object>().map((e) => e.toString()).join(' ')
            : value?.toString() ?? '';
        if (text.isEmpty) return;
        if (key == 'detail' || key == 'non_field_errors') {
          general ??= text;
        } else {
          fields['$prefix$key'] = text;
        }
      });
    }

    if (body is Map<String, dynamic>) collect(body, '');

    if (general == null && fields.isEmpty) {
      general = switch (status) {
        429 => 'Too many attempts. Please wait a minute and try again.',
        >= 500 => 'MindCare is having trouble right now. Please try again shortly.',
        _ => 'Something went wrong. Please try again.',
      };
    }
    return AuthException(
      general ?? 'Please check the highlighted fields.',
      fieldErrors: fields,
    );
  }

  @override
  String toString() => 'AuthException($message, $fieldErrors)';
}
