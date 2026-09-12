import 'package:share_plus/share_plus.dart';

/// Thin wrapper around share_plus so the rest of the app doesn't
/// import the package directly, and so share text is composed
/// consistently in one place.
class ShareService {
  ShareService._();
  static final instance = ShareService._();

  Future<void> shareText(String text, {String? subject}) async {
    await Share.share(text, subject: subject);
  }
}