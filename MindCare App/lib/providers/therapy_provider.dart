import 'package:flutter/material.dart';
import '../core/utils/date_labels.dart';
import '../models/therapy_data.dart';

class TherapyProvider extends ChangeNotifier {
  // ----- Browse -----
  /// Psychologists from the directory (GET /psychologists/directory/).
  /// Empty until loaded; the Care tab shows an empty state.
  List<Therapist> therapists = const [];

  void setTherapists(List<Therapist> list) {
    therapists = list;
    notifyListeners();
  }

  static const List<String> filterChips = ['All', 'Anxiety', 'Depression', 'Couples', 'Trauma'];
  String selectedFilter = 'All';
  String searchQuery = '';

  void setFilter(String filter) {
    selectedFilter = filter;
    notifyListeners();
  }

  void setSearchQuery(String query) {
    searchQuery = query;
    notifyListeners();
  }

  // ----- Sort & extra filters -----
  /// 'default' | 'rating' | 'price_low' | 'trial' | 'language'
  String sortMode = 'default';
  String? languageFilter;

  static const List<String> availableLanguages = ['English', 'Urdu', 'Pashto'];

  void setSortMode(String mode) {
    sortMode = mode;
    // Choosing a sort mode other than the language filter clears any
    // active language filter, so only one refinement applies at a
    // time — keeps the UI predictable rather than silently stacking.
    if (mode != 'language') languageFilter = null;
    notifyListeners();
  }

  void setLanguageFilter(String? language) {
    languageFilter = language;
    sortMode = language == null ? 'default' : 'language';
    notifyListeners();
  }

  List<Therapist> get filteredTherapists {
    var results = therapists.where((t) {
      final matchesFilter =
          selectedFilter == 'All' || t.specialty.toLowerCase().contains(selectedFilter.toLowerCase());
      final matchesSearch = searchQuery.isEmpty ||
          t.name.toLowerCase().contains(searchQuery.toLowerCase()) ||
          t.specialty.toLowerCase().contains(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    }).toList();

    switch (sortMode) {
      case 'rating':
        results.sort((a, b) => b.rating.compareTo(a.rating));
        break;
      case 'price_low':
        results.sort((a, b) => a.priceMonthly.compareTo(b.priceMonthly));
        break;
      case 'trial':
        results = results.where((t) => t.trialAvailable).toList();
        break;
      case 'language':
        if (languageFilter != null) {
          final shortCode = _languageShortCode(languageFilter!);
          results = results.where((t) => t.languages.contains(shortCode)).toList();
        }
        break;
      case 'default':
      default:
        break;
    }

    return results;
  }

  String _languageShortCode(String language) {
    switch (language) {
      case 'English':
        return 'En';
      case 'Urdu':
        return 'Ur';
      case 'Pashto':
        return 'Pa';
      default:
        return language;
    }
  }

  // ----- Bookmarks -----
  Set<String> bookmarkedTherapistIds = {};

  bool isBookmarked(String therapistId) => bookmarkedTherapistIds.contains(therapistId);

  void toggleBookmark(String therapistId) {
    if (bookmarkedTherapistIds.contains(therapistId)) {
      bookmarkedTherapistIds.remove(therapistId);
    } else {
      bookmarkedTherapistIds.add(therapistId);
    }
    notifyListeners();
  }

  // ----- Next session (Home) -----
  // Null until the backend reports a booked session.
  UpcomingSession? upcomingSession;

  void setUpcomingSession(UpcomingSession? session) {
    upcomingSession = session;
    notifyListeners();
  }

  // ----- Plan & trial -----
  Therapist? selectedTherapist;
  String selectedPlanId = 'monthly';

  void selectTherapist(Therapist therapist) {
    selectedTherapist = therapist;
    selectedPlanId = 'monthly';
    notifyListeners();
  }

  void selectPlan(String planId) {
    selectedPlanId = planId;
    notifyListeners();
  }

  // ----- Schedule -----
  /// Sessions used and included this month, once the plan is known.
  int? sessionsUsed;
  int? sessionsTotal;

  void setPlanUsage({required int used, required int total}) {
    sessionsUsed = used;
    sessionsTotal = total;
    notifyListeners();
  }

  /// The next seven days, starting today.
  static List<WeekDay> get weekDays {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    return List.generate(7, (i) => WeekDay(today.add(Duration(days: i))));
  }

  int selectedDayIndex = 0;

  static String _dayKey(DateTime d) => '${d.year}-${d.month}-${d.day}';

  /// The psychologist's open, booked and off slots per day, from the backend.
  Map<String, List<ScheduleSlot>> _availability = const {};

  void setAvailability(Map<DateTime, List<ScheduleSlot>> byDay) {
    _availability = {for (final e in byDay.entries) _dayKey(e.key): e.value};
    notifyListeners();
  }

  List<ScheduleSlot> availabilityFor(DateTime day) => _availability[_dayKey(day)] ?? const [];

  List<ScheduleSlot> get availabilityForSelectedDay => availabilityFor(weekDays[selectedDayIndex].day);

  String? selectedSlotTime;

  void selectDay(int index) {
    selectedDayIndex = index;
    selectedSlotTime = null;
    notifyListeners();
  }

  void selectSlot(String time, String status) {
    if (status != 'free') return;
    selectedSlotTime = time;
    notifyListeners();
  }

  /// Requests sent to the psychologist that they haven't answered yet.
  List<SessionRequest> pendingRequests = const [];

  Future<void> requestSession() async {
    final time = selectedSlotTime;
    if (time == null) return;
    // The backend request goes here; the psychologist confirms or declines.
    pendingRequests = [
      SessionRequest(day: weekDays[selectedDayIndex].day, time: time, requestedAt: DateTime.now()),
      ...pendingRequests,
    ];
    selectedSlotTime = null;
    notifyListeners();
  }

  // ----- Next confirmed session -----
  /// "Fri · 5:00 PM" for the confirmed session, or null if there is none.
  String? get nextConfirmedLabel {
    final s = upcomingSession;
    if (s == null) return null;
    return '${DateLabels.weekdayShort(s.startsAt)} · ${DateLabels.time(s.startsAt)}';
  }

  bool nextConfirmedCancelled = false;

  /// Asks the psychologist to move the confirmed session. It stays as it is
  /// until they accept.
  Future<void> rescheduleSession(WeekDay day, String time) async {
    pendingRequests = [
      SessionRequest(day: day.day, time: time, requestedAt: DateTime.now(), isReschedule: true),
      ...pendingRequests,
    ];
    notifyListeners();
  }

  Future<void> cancelSession(String note) async {
    // The backend cancellation (with the note) goes here.
    upcomingSession = null;
    nextConfirmedCancelled = true;
    notifyListeners();
  }
}
