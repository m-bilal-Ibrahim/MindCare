import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/checkin_data.dart';

class CheckinProvider extends ChangeNotifier {

  // ----- Daily mood (Home) -----
  static const List<DailyMoodOption> dailyMoods = [
    DailyMoodOption('bright', 'Bright', AppColors.dailyBright),
    DailyMoodOption('okay', 'Okay', AppColors.dailyOkay),
    DailyMoodOption('wobbly', 'Wobbly', AppColors.dailyWobbly),
    DailyMoodOption('heavy', 'Heavy', AppColors.dailyHeavy),
    DailyMoodOption('lost', 'Lost', AppColors.dailyLost),
  ];

  String? selectedDailyMoodId;

  void selectDailyMood(String id) {
    selectedDailyMoodId = selectedDailyMoodId == id ? null : id;
    notifyListeners();
  }

  // ----- Vitals -----
  // Built only from real sensor readings fed in through [addReading] /
  // [addReadings]. With no readings, [vitals] is null and screens show an
  // empty state instead of made-up numbers.

  /// How many recent readings the trend graphs and the calm strip show.
  static const int trendWindow = 12;

  // Adult resting upper limits. A reading at or above either one counts as
  // "activated". Replace with a per-user baseline or the AI model's output
  // once the backend provides one.
  static const int activatedHeartRate = 100;
  static const int activatedBreathingRate = 20;

  final List<VitalReading> _readings = [];

  List<VitalReading> get readings => List.unmodifiable(_readings);

  void addReading(VitalReading reading) => addReadings([reading]);

  void addReadings(Iterable<VitalReading> readings) {
    _readings
      ..addAll(readings)
      ..sort((a, b) => a.at.compareTo(b.at));
    // Keep a little more than the graphs need so the window stays full.
    if (_readings.length > trendWindow * 4) {
      _readings.removeRange(0, _readings.length - trendWindow * 4);
    }
    notifyListeners();
  }

  void clearReadings() {
    _readings.clear();
    notifyListeners();
  }

  static NervousSystemState classify(VitalReading r) =>
      r.heartRate >= activatedHeartRate || r.breathingRate >= activatedBreathingRate
          ? NervousSystemState.activated
          : NervousSystemState.calm;

  List<VitalReading> get _recent =>
      _readings.length <= trendWindow ? _readings : _readings.sublist(_readings.length - trendWindow);

  VitalsSnapshot? get vitals {
    if (_readings.isEmpty) return null;
    final recent = _recent;
    final latest = recent.last;
    // Steps are a running daily total, so only today's readings belong in the graph.
    final now = DateTime.now();
    final todaySteps = recent
        .where((r) => r.steps != null && r.at.year == now.year && r.at.month == now.month && r.at.day == now.day)
        .map((r) => r.steps!.toDouble())
        .toList();
    return VitalsSnapshot(
      heartRate: latest.heartRate,
      breathingRate: latest.breathingRate,
      steps: todaySteps.isEmpty ? null : todaySteps.last.round(),
      heartTrend: recent.map((r) => r.heartRate.toDouble()).toList(),
      breathingTrend: recent.map((r) => r.breathingRate.toDouble()).toList(),
      stepsTrend: todaySteps,
      state: classify(latest),
    );
  }

  List<NervousSystemState> get calmActivated => _recent.map(classify).toList();

  /// A gap longer than this between readings isn't counted as calm time,
  /// since we don't know what happened while the sensor was off.
  static const Duration _maxReadingGap = Duration(minutes: 15);

  /// Calm time today from sensor readings: each calm reading counts until
  /// the next one (capped), plus the share of today's readings that were
  /// calm. Null when there are no readings today.
  ({Duration calm, double share})? get calmToday {
    final now = DateTime.now();
    final today = _readings.where((r) => r.at.year == now.year && r.at.month == now.month && r.at.day == now.day).toList();
    if (today.isEmpty) return null;
    var calm = Duration.zero;
    for (var i = 0; i < today.length; i++) {
      if (classify(today[i]) != NervousSystemState.calm) continue;
      final next = i + 1 < today.length ? today[i + 1].at : now;
      final gap = next.difference(today[i].at);
      calm += gap > _maxReadingGap ? _maxReadingGap : gap;
    }
    final calmCount = today.where((r) => classify(r) == NervousSystemState.calm).length;
    return (calm: calm, share: calmCount / today.length);
  }

  // ----- Progress -----
  // Built from the patient's own check-ins once the backend stores them.
  int streakDays = 0;
  double? avgMood;
  double? avgMoodDelta;

  String moodRange = '30d';

  /// Mood values from 0 (heavy) to 1 (bright) per range, with axis labels.
  Map<String, List<double>> _moodSeries = const {};
  Map<String, List<String>> _moodLabels = const {};

  List<double> get moodTimeline => _moodSeries[moodRange] ?? const [];
  List<String> get moodTimelineLabels => _moodLabels[moodRange] ?? const [];

  void setMoodRange(String range) {
    moodRange = range;
    notifyListeners();
  }

  void setProgress({
    required int streak,
    double? average,
    double? averageDelta,
    Map<String, List<double>> series = const {},
    Map<String, List<String>> labels = const {},
    List<ProgressInsight> newInsights = const [],
  }) {
    streakDays = streak;
    avgMood = average;
    avgMoodDelta = averageDelta;
    _moodSeries = series;
    _moodLabels = labels;
    insights = newInsights;
    notifyListeners();
  }

  /// Patterns found in the patient's data (therapist-approved).
  List<ProgressInsight> insights = const [];

  // ----- Aida chat -----
  // The conversation starts empty. Replies come from the AI backend through
  // [replyHandler]; until that exists the app says so plainly instead of
  // inventing an answer.
  final List<ChatMessage> messages = [];
  bool isAssistantTyping = false;
  int _idCounter = 0;

  /// Sends the patient's message to the AI backend and returns Aida's reply.
  /// It must call a backend endpoint over HTTPS (never a model API key in
  /// the app), and chat content is sensitive health data.
  Future<String> Function(String message)? replyHandler;

  bool get aidaConnected => replyHandler != null;

  static const String notConnectedReply =
      "I can't reply yet because my chat is still being set up. If you need support right now, tap SOS or message your therapist.";

  String _nextId() => 'msg_${_idCounter++}';

  static const List<String> quickReplies = [
    'Help me name the feeling',
    "I don't want to journal",
    'Show me a calmer evening routine',
  ];

  Future<void> sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;

    messages.add(ChatMessage(id: _nextId(), sender: MessageSender.user, text: trimmed, timestamp: DateTime.now()));
    final handler = replyHandler;
    if (handler == null) {
      messages.add(ChatMessage(id: _nextId(), sender: MessageSender.assistant, text: notConnectedReply, timestamp: DateTime.now()));
      notifyListeners();
      return;
    }

    isAssistantTyping = true;
    notifyListeners();
    String reply;
    try {
      reply = await handler(trimmed);
    } catch (_) {
      reply = "Sorry, I couldn't reach MindCare just now. Please try again in a moment.";
    }
    messages.add(ChatMessage(id: _nextId(), sender: MessageSender.assistant, text: reply, timestamp: DateTime.now()));
    isAssistantTyping = false;
    notifyListeners();
  }
}
