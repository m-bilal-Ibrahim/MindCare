import 'package:flutter/material.dart';

import '../models/program_data.dart';

/// Care plan, daily wellbeing and Motivation Corner content.
///
/// Everything starts empty: the care plan is set by the therapist and the
/// rest comes from the backend, so screens show empty states until the
/// matching `set…` method is called with real data. Steps and calm time
/// come from sensor readings in CheckinProvider, not from here.
class ProgramProvider extends ChangeNotifier {
  // ----- Weekly care plan (set by therapist) -----
  List<WeeklyTask> weeklyTasks = const [];

  int get totalDone => weeklyTasks.fold(0, (sum, t) => sum + t.done);
  int get totalTasks => weeklyTasks.fold(0, (sum, t) => sum + t.total);

  void setWeeklyTasks(List<WeeklyTask> tasks) {
    weeklyTasks = tasks;
    notifyListeners();
  }

  // ----- Wellbeing -----

  /// Daily step totals for recent days, oldest first, with their labels.
  List<int> movementByDay = const [];
  List<String> movementDayLabels = const [];

  /// Change in steps versus the previous week, if the backend computes it.
  int? stepsChangePercent;

  /// A movement tip from the care plan or therapist-approved AI
  /// recommendations, if any.
  String? movementTip;

  void setMovementHistory({required List<int> steps, required List<String> labels, int? changePercent}) {
    movementByDay = steps;
    movementDayLabels = labels;
    stepsChangePercent = changePercent;
    notifyListeners();
  }

  void setMovementTip(String? tip) {
    movementTip = tip;
    notifyListeners();
  }

  /// Breakfast, lunch, snack, dinner for today; null until anything is logged.
  List<bool>? mealsDone;
  String? mealNote; // e.g. "Dinner — 8 PM" from the care plan

  void setMeals(List<bool>? meals, {String? note}) {
    mealsDone = meals;
    mealNote = note;
    notifyListeners();
  }

  /// Glasses of water today and the daily goal; null until known.
  int? waterGlassesFilled;
  int? waterGlassesGoal;

  void setWater({required int filled, required int goal}) {
    waterGlassesFilled = filled;
    waterGlassesGoal = goal;
    notifyListeners();
  }

  /// Today's small steps from the care plan.
  List<DailyStep> smallSteps = const [];

  void setSmallSteps(List<DailyStep> steps) {
    smallSteps = steps;
    notifyListeners();
  }

  void toggleSmallStep(int index) {
    if (index < 0 || index >= smallSteps.length) return;
    final s = smallSteps[index];
    smallSteps = [...smallSteps]..[index] = DailyStep(s.label, !s.done);
    notifyListeners();
  }

  // ----- Motivation -----
  static const List<String> motivationTabs = ['Duas', 'Quotes', 'Surahs'];
  String selectedMotivationTab = 'Duas';

  void setMotivationTab(String tab) {
    selectedMotivationTab = tab;
    notifyListeners();
  }

  /// Today's quote, e.g. from GET /motivation/quotes/random/.
  String? todayQuote;
  String? todayQuoteReference;

  void setTodayQuote(String? quote, {String? reference}) {
    todayQuote = quote;
    todayQuoteReference = reference;
    notifyListeners();
  }

  /// Duas and surahs with audio, served by the backend.
  AudioTrack? featuredTrack;
  List<AudioTrack> moreTracks = const [];

  void setTracks({AudioTrack? featured, List<AudioTrack> more = const []}) {
    featuredTrack = featured;
    moreTracks = more;
    notifyListeners();
  }

  List<AudioTrack> get allTracks => [if (featuredTrack != null) featuredTrack!, ...moreTracks];

  /// Unified playback: the id of whichever track is currently
  /// "playing" (featured or from the list) — only one at a time.
  /// Null means nothing is playing.
  String? playingTrackId;

  bool isPlaying(String trackId) => playingTrackId == trackId;

  void togglePlay(String trackId) {
    playingTrackId = playingTrackId == trackId ? null : trackId;
    notifyListeners();
  }

  /// Bookmarked tracks — shown as filled once saved.
  Set<String> bookmarkedTrackIds = {};

  bool isTrackBookmarked(String trackId) => bookmarkedTrackIds.contains(trackId);

  List<AudioTrack> get bookmarkedTracks => allTracks.where((track) => bookmarkedTrackIds.contains(track.id)).toList();

  void toggleTrackBookmark(String trackId) {
    if (bookmarkedTrackIds.contains(trackId)) {
      bookmarkedTrackIds.remove(trackId);
    } else {
      bookmarkedTrackIds.add(trackId);
    }
    notifyListeners();
  }
}
