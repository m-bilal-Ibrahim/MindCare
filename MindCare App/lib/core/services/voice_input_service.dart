import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Thin wrapper around speech_to_text so the rest of the app doesn't
/// import the package directly, and so permission/init handling is
/// consistent in one place.
///
/// NOTE: this uses on-device / browser-native speech recognition
/// (the Web Speech API on Chrome, iOS/Android's system speech engine
/// when built for those platforms) — audio is not sent to any
/// third-party transcription service by this package. If MindCare
/// later adds a custom transcription backend, treat spoken content
/// as sensitive health data with the same care as typed chat: HTTPS
/// only, no plaintext logging, encrypted at rest.
class VoiceInputService {
  VoiceInputService._();
  static final instance = VoiceInputService._();

  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;

  Future<bool> initialize() async {
    if (_isInitialized) return true;
    _isInitialized = await _speech.initialize(
      onError: (_) {},
      onStatus: (_) {},
    );
    return _isInitialized;
  }

  bool get isListening => _speech.isListening;
  bool get isAvailable => _speech.isAvailable;

  Future<bool> startListening({
    required void Function(String text, bool isFinal) onResult,
  }) async {
    final ready = await initialize();
    if (!ready) return false;

    await _speech.listen(
      onResult: (result) {
        onResult(result.recognizedWords, result.finalResult);
      },
      listenOptions: stt.SpeechListenOptions(
        partialResults: true,
        cancelOnError: true,
      ),
    );
    return true;
  }

  Future<void> stopListening() async {
    await _speech.stop();
  }

  Future<void> cancelListening() async {
    await _speech.cancel();
  }
}