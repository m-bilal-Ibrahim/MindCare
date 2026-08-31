import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/account_data.dart';

class AccountProvider extends ChangeNotifier {
  // ----- Rewards -----
  final int levelNumber = 4;
  final String levelName = 'Centered';
  final String nextLevelName = 'Settled';
  final int currentPoints = 620;
  final int nextLevelPoints = 1000;

  final int checkinStreak = 14;
  final int statsSessions = 8;
  final int statsExercises = 32;
  final int statsJournals = 12;

  final List<RewardBadge> badges = const [
    RewardBadge(
      icon: Icons.directions_walk,
      iconColor: Color(0xFFCB8B57),
      name: 'First step',
      unlocked: true,
      description: 'Awarded for completing your very first check-in on MindCare.',
      criteria: 'Complete 1 daily check-in.',
      unlockedDate: 'Feb 14, 2026',
    ),
    RewardBadge(
      icon: Icons.chat_bubble,
      iconColor: Color(0xFF3FA79A),
      name: '7-day calm',
      unlocked: true,
      description: 'You showed up for seven days in a row, even on the harder ones.',
      criteria: 'Check in 7 days in a row.',
      unlockedDate: 'Feb 21, 2026',
    ),
    RewardBadge(
      icon: Icons.favorite,
      iconColor: Color(0xFFB85E4E),
      name: 'First session',
      unlocked: true,
      description: 'You took the step of completing your first therapy session.',
      criteria: 'Complete 1 therapy session.',
      unlockedDate: 'Mar 2, 2026',
    ),
    RewardBadge(
      icon: Icons.nightlight_round,
      iconColor: Color(0xFF6B6FC7),
      name: 'Night owl',
      unlocked: true,
      description: 'Five check-ins logged after 10 PM — MindCare is there whenever you need it.',
      criteria: 'Check in after 10 PM, 5 times.',
      unlockedDate: 'Mar 19, 2026',
    ),
    RewardBadge(
      icon: Icons.lock_outline,
      iconColor: Color(0xFFB8AF9C),
      name: 'Open heart',
      unlocked: false,
      description: 'For sharing a journal entry with your therapist for the first time.',
      criteria: 'Share 1 journal entry with your therapist.',
    ),
    RewardBadge(
      icon: Icons.lock_outline,
      iconColor: Color(0xFFB8AF9C),
      name: 'Mountain',
      unlocked: false,
      description: 'For completing 30 days of check-ins, consecutive or not, over any span.',
      criteria: 'Complete 30 total check-ins.',
    ),
  ];
  final int badgesUnlocked = 4;
  final int badgesTotal = 12;

    List<EarnTask> earnTasks = const [
    EarnTask(title: 'Daily check-in', subtitle: 'Pick a mood, anything.', points: 10, done: true),
    EarnTask(title: 'Complete an exercise', subtitle: 'Any breath or body scan.', points: 15, done: false),
    EarnTask(title: 'Journal an entry', subtitle: 'A few lines is enough.', points: 20, done: false),
  ];

  /// Marks an "earn today" task done, awarding its points once.
  /// Tapping an already-done task does nothing — points aren't
  /// re-awarded for the same task twice in a day.
  void completeEarnTask(int index) {
    final task = earnTasks[index];
    if (task.done) return;
    earnTasks = List.generate(earnTasks.length, (i) {
      return i == index ? EarnTask(title: task.title, subtitle: task.subtitle, points: task.points, done: true) : earnTasks[i];
    });
    notifyListeners();
  }
  // ----- Wallet -----
  int walletBalance = 2450;
  final String walletBalanceNote = '≈ 1 short session';

  final Map<String, dynamic> upcomingCharge = const {
    'therapistInitials': 'TM',
    'therapistColor': AppColors.moodStressed,
    'title': 'Session · Dr. Tariq',
    'subtitle': 'Fri, May 23 · 5:00 PM',
    'amount': 'Rs 4,500',
    'note': 'auto · Mastercard',
  };

  bool autoRenewEnabled = true;

  void setAutoRenew(bool value) {
    autoRenewEnabled = value;
    notifyListeners();
  }

  List<PaymentMethod> paymentMethods = [
    const PaymentMethod(
      id: 'mc',
      name: 'Mastercard',
      lastFour: '3414',
      expiry: '09 / 27',
      isDefault: true,
      gradientColors: [Color(0xFF7A2E22), Color(0xFF4A1712)],
    ),
    const PaymentMethod(
      id: 'ep',
      name: 'Easypaisa',
      lastFour: '7821',
      expiry: '09 / 27',
      isDefault: false,
      gradientColors: [Color(0xFF2C6E4A), Color(0xFF184630)],
    ),
  ];

  List<WalletTransaction> transactions = const [
    WalletTransaction(
      icon: Icons.terrain,
      iconBackground: Color(0xFFEFE7D6),
      title: 'Session · Dr. Sana',
      subtitle: 'May 16 · 50 min',
      amount: 'Rs −4,500',
      isCredit: false,
    ),
    WalletTransaction(
      icon: Icons.arrow_downward,
      iconBackground: Color(0xFFEFE7D6),
      title: 'Top up · Mastercard',
      subtitle: 'May 14',
      amount: 'Rs +5,000',
      isCredit: true,
    ),
    WalletTransaction(
      icon: Icons.explore_outlined,
      iconBackground: Color(0xFFEFE7D6),
      title: 'Plan upgrade · Quarterly',
      subtitle: 'May 1 · auto-renews Aug',
      amount: 'Rs −7,000',
      isCredit: false,
    ),
    WalletTransaction(
      icon: Icons.local_fire_department,
      iconBackground: Color(0xFFF0DEB9),
      title: 'Streak reward · 14 days',
      subtitle: 'Apr 28',
      amount: 'Rs +200',
      isCredit: true,
    ),
    WalletTransaction(
      icon: Icons.terrain,
      iconBackground: Color(0xFFEFE7D6),
      title: 'Session · Dr. Tariq',
      subtitle: 'Apr 20 · 50 min',
      amount: 'Rs −4,500',
      isCredit: false,
    ),
    WalletTransaction(
      icon: Icons.arrow_downward,
      iconBackground: Color(0xFFEFE7D6),
      title: 'Top up · Easypaisa',
      subtitle: 'Apr 10',
      amount: 'Rs +3,000',
      isCredit: true,
    ),
  ];

  Future<void> topUp(int amount) async {
    await Future.delayed(const Duration(milliseconds: 400));
    walletBalance += amount;
    transactions = [
      WalletTransaction(
        icon: Icons.arrow_downward,
        iconBackground: const Color(0xFFEFE7D6),
        title: 'Top up · ${paymentMethods.firstWhere((p) => p.isDefault, orElse: () => paymentMethods.first).name}',
        subtitle: 'Just now',
        amount: 'Rs +$amount',
        isCredit: true,
      ),
      ...transactions,
    ];
    notifyListeners();
  }

  /// Returns false if the withdrawal would exceed the balance —
  /// caller should show an error rather than proceed.
  Future<bool> withdraw(int amount) async {
    if (amount > walletBalance) return false;
    await Future.delayed(const Duration(milliseconds: 400));
    walletBalance -= amount;
    transactions = [
      WalletTransaction(
        icon: Icons.arrow_upward,
        iconBackground: const Color(0xFFEFE7D6),
        title: 'Withdrawal · ${paymentMethods.firstWhere((p) => p.isDefault, orElse: () => paymentMethods.first).name}',
        subtitle: 'Just now',
        amount: 'Rs −$amount',
        isCredit: false,
      ),
      ...transactions,
    ];
    notifyListeners();
    return true;
  }

  void addPaymentMethod({required String name, required String lastFour, required String expiry}) {
    final colors = _colorsForCardName(name);
    paymentMethods = [
      ...paymentMethods,
      PaymentMethod(id: 'pm_${DateTime.now().millisecondsSinceEpoch}', name: name, lastFour: lastFour, expiry: expiry, isDefault: false, gradientColors: colors),
    ];
    notifyListeners();
  }

  void setDefaultPaymentMethod(String id) {
    paymentMethods = paymentMethods.map((m) {
      return PaymentMethod(id: m.id, name: m.name, lastFour: m.lastFour, expiry: m.expiry, isDefault: m.id == id, gradientColors: m.gradientColors);
    }).toList();
    notifyListeners();
  }

  /// Won't remove the last remaining payment method — returns false
  /// if the removal was blocked for that reason.
  bool removePaymentMethod(String id) {
    if (paymentMethods.length <= 1) return false;
    final wasDefault = paymentMethods.firstWhere((m) => m.id == id).isDefault;
    paymentMethods = paymentMethods.where((m) => m.id != id).toList();
    if (wasDefault && paymentMethods.isNotEmpty) {
      final firstId = paymentMethods.first.id;
      paymentMethods = paymentMethods.map((m) {
        return PaymentMethod(id: m.id, name: m.name, lastFour: m.lastFour, expiry: m.expiry, isDefault: m.id == firstId, gradientColors: m.gradientColors);
      }).toList();
    }
    notifyListeners();
    return true;
  }

  List<Color> _colorsForCardName(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('visa')) return [const Color(0xFF264A73), const Color(0xFF122A47)];
    if (lower.contains('easypaisa')) return [const Color(0xFF2C6E4A), const Color(0xFF184630)];
    if (lower.contains('jazzcash')) return [const Color(0xFFB8324A), const Color(0xFF6E1C2C)];
    return [const Color(0xFF5A5040), const Color(0xFF33301E)];
  }

  // ----- Profile -----
  final String userName = 'Layla Siddiqui';
  final String joinedInfo = 'Joined Feb 2026 · Islamabad';
  final String therapistName = 'Dr. Tariq Mahmood';
  final String therapistSince = 'since Feb 2026';

  String aidaPersonality = 'Gentle';

  void setAidaPersonality(String personality) {
    aidaPersonality = personality;
    notifyListeners();
  }

  final int pastSessionsCount = 8;
  final bool wearableConnected = true;
  final bool notificationsOn = true;

  // ----- Circle contacts -----
  List<CircleContact> circleContacts = const [
    CircleContact(name: 'Ammi', relation: 'Mother', avatarColor: Color(0xFFE5382B)),
    CircleContact(name: 'Hira', relation: 'Sister', avatarColor: Color(0xFF3FA79A)),
    CircleContact(name: 'Zoya', relation: 'Close friend', avatarColor: Color(0xFF8B90D9)),
  ];

  Future<void> notifyCircle(List<String> names) async {
    await Future.delayed(const Duration(milliseconds: 700));
    circleContacts = circleContacts
        .map((c) => names.contains(c.name) ? c.copyWith(notified: true) : c)
        .toList();
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

  // ----- Past sessions -----
  final List<PastSession> pastSessions = const [
    PastSession(
      therapistName: 'Dr. Tariq Mahmood',
      date: 'May 16, 2026',
      durationMinutes: 50,
      summary: 'Discussed work stress patterns and practiced a grounding technique for meetings.',
      hasSharedNotes: true,
    ),
    PastSession(
      therapistName: 'Dr. Tariq Mahmood',
      date: 'May 2, 2026',
      durationMinutes: 50,
      summary: 'Follow-up on sleep routine changes. Reported improved sleep onset.',
      hasSharedNotes: true,
    ),
    PastSession(
      therapistName: 'Dr. Tariq Mahmood',
      date: 'Apr 18, 2026',
      durationMinutes: 45,
      summary: 'Introduced box breathing as a pre-meeting regulation tool.',
      hasSharedNotes: false,
    ),
    PastSession(
      therapistName: 'Dr. Sana Aftab',
      date: 'Apr 4, 2026',
      durationMinutes: 50,
      summary: 'Initial intake session. Established goals for the next quarter.',
      hasSharedNotes: true,
    ),
  ];

  // ----- Therapist bio -----
  final TherapistProfile therapistProfile = const TherapistProfile(
    name: 'Dr. Tariq Mahmood',
    credentials: 'PsyD, Licensed Clinical Psychologist',
    since: 'Working with you since Feb 2026',
    bio: 'Dr. Mahmood specializes in anxiety, work-related stress, and sleep difficulties, using an integrative approach that combines CBT with mindfulness-based techniques. He believes therapy works best as a steady, collaborative process rather than a quick fix.',
    specialties: ['Anxiety', 'Work stress', 'Sleep', 'CBT', 'Mindfulness'],
    languages: ['English', 'Urdu'],
    rating: 4.9,
    sessionsWithYou: 6,
  );

  // ----- Past programs (for "View past programs") -----
  final List<Map<String, String>> pastPrograms = const [
    {'title': 'Sleep reset program', 'period': 'Jan – Feb 2026', 'setBy': 'Dr. Tariq Mahmood'},
    {'title': 'Initial stabilization plan', 'period': 'Feb 2026', 'setBy': 'Dr. Sana Aftab'},
  ];
}