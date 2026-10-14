import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../security/secure_storage_service.dart';
import 'auth_api.dart';

/// Signed-in calls to the MindCare backend.
///
/// Sends the stored access token. When the server answers 401 it refreshes
/// the tokens once (the backend rotates the refresh token, so both are
/// saved) and retries; if that fails too it throws [ApiException.sessionExpired]
/// so the screen can send the patient back to sign in.
class ApiClient {
  ApiClient({http.Client? client, TokenStore? tokens})
      : _client = client ?? http.Client(),
        _tokens = tokens ?? const SecureTokenStore();

  static final ApiClient instance = ApiClient();

  final http.Client _client;
  final TokenStore _tokens;

  /// Render's free tier sleeps when idle; the first request can take ~a minute.
  static const Duration _timeout = Duration(seconds: 90);

  Future<void>? _refreshing;

  Future<Object?> get(String path, {Map<String, String>? query}) => _send('GET', path, query: query);

  Future<Object?> put(String path, Map<String, dynamic> body) => _send('PUT', path, body: body);

  Future<Object?> _send(String method, String path, {Map<String, String>? query, Map<String, dynamic>? body}) async {
    var response = await _request(method, path, query: query, body: body);
    if (response.statusCode == 401) {
      await _refreshTokens();
      response = await _request(method, path, query: query, body: body);
      if (response.statusCode == 401) throw const ApiException.sessionExpired();
    }
    final decoded = _decode(response.bodyBytes);
    if (response.statusCode >= 200 && response.statusCode < 300) return decoded;
    throw ApiException.fromResponse(response.statusCode, decoded);
  }

  Future<http.Response> _request(String method, String path, {Map<String, String>? query, Map<String, dynamic>? body}) async {
    final access = await _tokens.access();
    if (access == null) throw const ApiException.sessionExpired();
    var uri = Uri.parse('${AuthApi.baseUrl}$path');
    if (query != null && query.isNotEmpty) uri = uri.replace(queryParameters: query);
    final headers = {
      'Authorization': 'Bearer $access',
      'Accept': 'application/json',
      if (body != null) 'Content-Type': 'application/json',
    };
    try {
      final request = http.Request(method, uri)..headers.addAll(headers);
      if (body != null) request.body = jsonEncode(body);
      final streamed = await _client.send(request).timeout(_timeout);
      return await http.Response.fromStream(streamed);
    } on TimeoutException {
      throw const ApiException(0, 'MindCare is taking too long to answer. Please try again.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const ApiException(0, "Couldn't reach MindCare's servers. Check your connection and try again.");
    }
  }

  /// One refresh at a time: parallel 401s wait for the same refresh.
  Future<void> _refreshTokens() => _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);

  Future<void> _doRefresh() async {
    final refresh = await _tokens.refresh();
    if (refresh == null) throw const ApiException.sessionExpired();
    final http.Response response;
    try {
      response = await _client
          .post(
            Uri.parse('${AuthApi.baseUrl}/accounts/refresh/'),
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode({'refresh': refresh}),
          )
          .timeout(_timeout);
    } catch (_) {
      throw const ApiException(0, "Couldn't reach MindCare's servers. Check your connection and try again.");
    }
    final decoded = _decode(response.bodyBytes);
    if (response.statusCode != 200 || decoded is! Map<String, dynamic> || decoded['access'] is! String) {
      await _tokens.clear();
      throw const ApiException.sessionExpired();
    }
    await _tokens.save(access: decoded['access'] as String, refresh: decoded['refresh'] as String?);
  }

  /// Decodes as UTF-8 regardless of the Content-Type charset, so Arabic
  /// text arrives intact.
  static Object? _decode(List<int> bytes) {
    if (bytes.isEmpty) return null;
    try {
      return jsonDecode(utf8.decode(bytes, allowMalformed: true));
    } catch (_) {
      return null;
    }
  }
}

/// Where the tokens live. Swapped for an in-memory store in tests.
abstract class TokenStore {
  Future<String?> access();
  Future<String?> refresh();
  Future<void> save({required String access, String? refresh});
  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  const SecureTokenStore();

  @override
  Future<String?> access() => SecureStorageService.instance.getAuthToken();

  @override
  Future<String?> refresh() => SecureStorageService.instance.getRefreshToken();

  @override
  Future<void> save({required String access, String? refresh}) async {
    await SecureStorageService.instance.saveAuthToken(access);
    if (refresh != null) await SecureStorageService.instance.saveRefreshToken(refresh);
  }

  @override
  Future<void> clear() => SecureStorageService.instance.clearAll();
}

/// A failed API call, with a message that can be shown as it is.
@immutable
class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  const ApiException.sessionExpired()
      : statusCode = 401,
        message = 'Your session has ended. Please sign in again.';

  final int statusCode;
  final String message;

  bool get isSessionExpired => statusCode == 401;

  factory ApiException.fromResponse(int status, Object? body) {
    String? detail;
    if (body is Map<String, dynamic>) {
      final d = body['detail'];
      if (d is String && d.isNotEmpty) detail = d;
      if (detail == null) {
        for (final value in body.values) {
          if (value is List && value.isNotEmpty) {
            detail = value.first.toString();
            break;
          }
        }
      }
    }
    final message = switch (status) {
      403 => detail ?? "You're not allowed to see this.",
      404 => detail ?? "This couldn't be found.",
      429 => 'Too many attempts. Please wait a minute and try again.',
      >= 500 => 'MindCare is having trouble right now. Please try again shortly.',
      _ => detail ?? 'Something went wrong. Please try again.',
    };
    return ApiException(status, message);
  }

  @override
  String toString() => 'ApiException($statusCode, $message)';
}
