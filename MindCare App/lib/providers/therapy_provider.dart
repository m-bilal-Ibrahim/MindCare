import 'package:flutter/material.dart';
import '../models/therapy_data.dart';

class TherapyProvider extends ChangeNotifier {
  // ----- Browse -----
  static const List<Therapist> therapists = [
    Therapist(
      id: 'tariq',
      name: 'Dr. Tariq Mahmood',
      initials: 'TM',
      avatarColor: Color(0xFFE5382B),
      title: 'Clinical psychologist · CBT, ACT',
      specialty: 'Anxiety · Burnout · CBT',
      rating: 4.9,
      reviewCount: 218,
      yearsExperience: 12,
      languages: 'En · Ur',
      priceMonthly: 18000,
      priceYearly: 180000,
      trialAvailable: true,
      status: 'Open',
      credentialBadge: 'PMDC',
    ),
    Therapist(
      id: 'sana',
      name: 'Dr. Sana Yousaf',
      initials: 'SY',
      avatarColor: Color(0xFF8E5FE0),
      title: 'Clinical psychologist',
      specialty: 'Depression · Grief',
      rating: 4.8,
      reviewCount: 142,
      yearsExperience: 8,
      languages: 'En · Ur',
      priceMonthly: 20000,
      priceYearly: 200000,
      trialAvailable: true,
      status: 'Open',
      credentialBadge: 'PMDC',
    ),
    Therapist(
      id: 'hira',
      name: 'Hira Khan, MSc',
      initials: 'HK',
      avatarColor: Color(0xFF1CB88A),
      title: 'Licensed counselor',
      specialty: 'Couples · Family',
      rating: 4.7,
      reviewCount: 96,
      yearsExperience: 6,
      languages: 'En · Ur · Pa',
      priceMonthly: 14000,
      priceYearly: 140000,
      trialAvailable: true,
      status: 'Open',
      credentialBadge: 'PMDC',
    ),
    Therapist(
      id: 'omar',
      name: 'Dr. Omar Raza',
      initials: 'OR',
      avatarColor: Color(0xFF2497D9),
      title: 'Clinical psychologist',
      specialty: 'Trauma · PTSD',
      rating: 4.6,
      reviewCount: 74,
      yearsExperience: 10,
      languages: 'En · Ur',
      priceMonthly: 26000,
      priceYearly: 260000,
      trialAvailable: false,
      status: 'Busy',
      credentialBadge: 'PMDC',
    ),
  ];

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

  List<Therapist> get filteredTherapists {
    return therapists.where((t) {
      final matchesFilter =
          selectedFilter == 'All' || t.specialty.toLowerCase().contains(selectedFilter.toLowerCase());
      final matchesSearch = searchQuery.isEmpty ||
          t.name.toLowerCase().contains(searchQuery.toLowerCase()) ||
          t.specialty.toLowerCase().contains(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    }).toList();
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
  final int sessionsUsed = 2;
  final int sessionsTotal = 4;

  static const List<WeekDay> weekDays = [
    WeekDay('Mon', 19),
    WeekDay('Tue', 20),
    WeekDay('Wed', 21),
    WeekDay('Thu', 22),
    WeekDay('Fri', 23),
    WeekDay('Sat', 24),
    WeekDay('Sun', 25),
  ];

  int selectedDayIndex = 2;

  static const List<ScheduleSlot> _daySlots = [
    ScheduleSlot('9:30 AM', 'booked'),
    ScheduleSlot('11:00 AM', 'free'),
    ScheduleSlot('12:30 PM', 'free'),
    ScheduleSlot('2:00 PM', 'booked'),
    ScheduleSlot('3:30 PM', 'free'),
    ScheduleSlot('5:00 PM', 'free'),
    ScheduleSlot('6:30 PM', 'booked'),
    ScheduleSlot('8:00 PM', 'off'),
  ];

  List<ScheduleSlot> get availabilityForSelectedDay => _daySlots;

  String? selectedSlotTime = '5:00 PM';

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

  /// Sends a session request to the backend.
  ///
  /// NOTE: demo/placeholder only. In production this must be a real,
  /// authenticated HTTPS call. The server — never the client — must
  /// be the source of truth for slot availability, to prevent double
  /// booking, and must generate the video-call link itself using a
  /// short-lived, single-use, per-session token rather than a static
  /// reusable link that could be shared or replayed.
  Future<void> requestSession() async {
    await Future.delayed(const Duration(milliseconds: 500));
    notifyListeners();
  }
}