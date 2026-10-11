import 'package:flutter/material.dart';
import '../models/account_data.dart';

/// Rewards, wallet, profile details, therapist, sessions and SOS contacts.
///
/// Nothing here is made up: counts start at zero, lists start empty and
/// the therapist is unknown until the backend says otherwise. The badge
/// and daily-task catalogues are part of the app's design, so they are
/// listed, but none is earned or done until real activity is recorded.
class AccountProvider extends ChangeNotifier {
  // ----- Rewards -----
  int levelNumber = 1;
  int currentPoints = 0;

  /// Points needed for the next level, once the rewards rules exist.
  int? nextLevelPoints;

  int checkinStreak = 0;
  int statsSessions = 0;
  int statsExercises = 0;
  int statsJournals = 0;

  /// Every badge that can be earned. [RewardBadge.unlocked] and
  /// [RewardBadge.unlockedDate] come from the backend.
  List<RewardBadge> badges = const [
    RewardBadge(
      icon: Icons.directions_walk,
      iconColor: Color(0xFFCB8B57),
      name: 'First step',
      unlocked: false,
      description: 'Awarded for completing your very first check-in on MindCare.',
      criteria: 'Complete 1 daily check-in.',
    ),
    RewardBadge(
      icon: Icons.chat_bubble,
      iconColor: Color(0xFF3FA79A),
      name: '7-day calm',
      unlocked: false,
      description: 'You showed up for seven days in a row, even on the harder ones.',
      criteria: 'Check in 7 days in a row.',
    ),
    RewardBadge(
      icon: Icons.favorite,
      iconColor: Color(0xFFB85E4E),
      name: 'First session',
      unlocked: false,
      description: 'You took the step of completing your first therapy session.',
      criteria: 'Complete 1 therapy session.',
    ),
    RewardBadge(
      icon: Icons.nightlight_round,
      iconColor: Color(0xFF6B6FC7),
      name: 'Night owl',
      unlocked: false,
      description: 'Five check-ins logged after 10 PM — MindCare is there whenever you need it.',
      criteria: 'Check in after 10 PM, 5 times.',
    ),
    RewardBadge(
      icon: Icons.visibility_outlined,
      iconColor: Color(0xFF7CA891),
      name: 'Open heart',
      unlocked: false,
      description: 'For sharing a journal entry with your therapist for the first time.',
      criteria: 'Share 1 journal entry with your therapist.',
    ),
    RewardBadge(
      icon: Icons.terrain,
      iconColor: Color(0xFF8A79EA),
      name: 'Mountain',
      unlocked: false,
      description: 'For completing 30 days of check-ins, consecutive or not, over any span.',
      criteria: 'Complete 30 total check-ins.',
    ),
  ];

  int get badgesUnlocked => badges.where((b) => b.unlocked).length;
  int get badgesTotal => badges.length;

  /// Ways to earn points today. A task is marked done only when the
  /// activity really happens (reported by the backend), not by tapping it.
  List<EarnTask> earnTasks = const [
    EarnTask(title: 'Daily check-in', subtitle: 'Pick a mood, anything.', points: 10, done: false),
    EarnTask(title: 'Complete an exercise', subtitle: 'Any breath or body scan.', points: 15, done: false),
    EarnTask(title: 'Journal an entry', subtitle: 'A few lines is enough.', points: 20, done: false),
  ];

  void setRewards({
    required int level,
    required int points,
    int? pointsForNextLevel,
    required int streak,
    required int sessions,
    required int exercises,
    required int journals,
    List<RewardBadge>? badgeStates,
    List<EarnTask>? todayTasks,
  }) {
    levelNumber = level;
    currentPoints = points;
    nextLevelPoints = pointsForNextLevel;
    checkinStreak = streak;
    statsSessions = sessions;
    statsExercises = exercises;
    statsJournals = journals;
    if (badgeStates != null) badges = badgeStates;
    if (todayTasks != null) earnTasks = todayTasks;
    notifyListeners();
  }

  // ----- Wallet -----
  /// Null until payments exist; the wallet screen shows an empty state.
  int? walletBalance;

  /// The next scheduled charge, as reported by the backend.
  WalletCharge? upcomingCharge;

  bool autoRenewEnabled = true;

  void setAutoRenew(bool value) {
    autoRenewEnabled = value;
    notifyListeners();
  }

  /// Cards the patient saved. Only brand, last four and expiry are kept.
  List<PaymentMethod> paymentMethods = const [];

  List<WalletTransaction> transactions = const [];

  void setWallet({int? balance, WalletCharge? nextCharge, List<WalletTransaction> history = const []}) {
    walletBalance = balance;
    upcomingCharge = nextCharge;
    transactions = history;
    notifyListeners();
  }

  void addPaymentMethod({required String name, required String lastFour, required String expiry}) {
    final colors = _colorsForCardName(name);
    paymentMethods = [
      ...paymentMethods,
      PaymentMethod(
        id: 'pm_${DateTime.now().millisecondsSinceEpoch}',
        name: name,
        lastFour: lastFour,
        expiry: expiry,
        isDefault: paymentMethods.isEmpty,
        gradientColors: colors,
      ),
    ];
    notifyListeners();
  }

  void setDefaultPaymentMethod(String id) {
    paymentMethods = paymentMethods.map((m) {
      return PaymentMethod(id: m.id, name: m.name, lastFour: m.lastFour, expiry: m.expiry, isDefault: m.id == id, gradientColors: m.gradientColors);
    }).toList();
    notifyListeners();
  }

  void removePaymentMethod(String id) {
    final wasDefault = paymentMethods.any((m) => m.id == id && m.isDefault);
    paymentMethods = paymentMethods.where((m) => m.id != id).toList();
    if (wasDefault && paymentMethods.isNotEmpty) {
      final firstId = paymentMethods.first.id;
      paymentMethods = paymentMethods.map((m) {
        return PaymentMethod(id: m.id, name: m.name, lastFour: m.lastFour, expiry: m.expiry, isDefault: m.id == firstId, gradientColors: m.gradientColors);
      }).toList();
    }
    notifyListeners();
  }

  List<Color> _colorsForCardName(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('visa')) return [const Color(0xFF264A73), const Color(0xFF122A47)];
    if (lower.contains('mastercard')) return [const Color(0xFF7A2E22), const Color(0xFF4A1712)];
    if (lower.contains('easypaisa')) return [const Color(0xFF2C6E4A), const Color(0xFF184630)];
    if (lower.contains('jazzcash')) return [const Color(0xFFB8324A), const Color(0xFF6E1C2C)];
    return [const Color(0xFF5A5040), const Color(0xFF33301E)];
  }

  // ----- Profile -----
  /// e.g. "Joined Oct 2026 · Islamabad", from the patient profile.
  String? joinedInfo;

  void setJoinedInfo(String? info) {
    joinedInfo = info;
    notifyListeners();
  }

  /// The patient's current psychologist (GET /relationships/current/), or
  /// null when they have none yet.
  TherapistProfile? therapistProfile;

  void setTherapist(TherapistProfile? therapist) {
    therapistProfile = therapist;
    notifyListeners();
  }

  String aidaPersonality = 'Gentle';

  void setAidaPersonality(String personality) {
    aidaPersonality = personality;
    notifyListeners();
  }

  bool wearableConnected = false;
  final bool notificationsOn = true;

  void setWearableConnected(bool connected) {
    wearableConnected = connected;
    notifyListeners();
  }

  // ----- Circle contacts (people SOS can notify) -----
  List<CircleContact> circleContacts = const [];

  void setCircleContacts(List<CircleContact> contacts) {
    circleContacts = contacts;
    notifyListeners();
  }

  Future<void> notifyCircle(List<String> names) async {
    // The backend sends the actual messages; this records who was notified.
    circleContacts = circleContacts.map((c) => names.contains(c.name) ? c.copyWith(notified: true) : c).toList();
    notifyListeners();
  }

  // ----- Aida personality options -----
  final List<AidaPersonalityOption> aidaPersonalityOptions = const [
    AidaPersonalityOption(
      name: 'Gentle',
      tagline: 'Soft, patient, never rushes you',
      description: 'Aida checks in slowly, uses warm language, and gives you space before offering suggestions. Good if directness feels like pressure.',
      icon: Icons.spa_outlined,
      color: Color(0xFF7CA891),
    ),
    AidaPersonalityOption(
      name: 'Direct',
      tagline: 'Clear, to the point, practical',
      description: 'Aida gets straight to what might help, with fewer check-in questions and more concrete next steps. Good if you prefer efficiency.',
      icon: Icons.bolt_outlined,
      color: Color(0xFFCB8B57),
    ),
    AidaPersonalityOption(
      name: 'Playful',
      tagline: 'Light, a little humor, still caring',
      description: 'Aida keeps things a little lighter when appropriate, without minimizing what you\'re going through. Good if heaviness feels like too much some days.',
      icon: Icons.emoji_emotions_outlined,
      color: Color(0xFFB85E4E),
    ),
    AidaPersonalityOption(
      name: 'Analytical',
      tagline: 'Structured, explains the \'why\'',
      description: 'Aida walks through the reasoning behind suggestions — what\'s happening physiologically, why an exercise helps. Good if understanding the mechanism helps you engage.',
      icon: Icons.insights_outlined,
      color: Color(0xFF6B6FC7),
    ),
  ];

  // ----- Past sessions and programs -----
  List<PastSession> pastSessions = const [];

  int get pastSessionsCount => pastSessions.length;

  /// Earlier care plans: title, period and who set them.
  List<PastProgram> pastPrograms = const [];

  void setHistory({List<PastSession> sessions = const [], List<PastProgram> programs = const []}) {
    pastSessions = sessions;
    pastPrograms = programs;
    notifyListeners();
  }
}
