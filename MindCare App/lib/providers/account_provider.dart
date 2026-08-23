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
    RewardBadge(icon: Icons.directions_walk, iconColor: Color(0xFFCB8B57), name: 'First step', unlocked: true),
    RewardBadge(icon: Icons.chat_bubble, iconColor: Color(0xFF3FA79A), name: '7-day calm', unlocked: true),
    RewardBadge(icon: Icons.favorite, iconColor: Color(0xFFB85E4E), name: 'First session', unlocked: true),
    RewardBadge(icon: Icons.nightlight_round, iconColor: Color(0xFF6B6FC7), name: 'Night owl', unlocked: true),
    RewardBadge(icon: Icons.lock_outline, iconColor: Color(0xFFB8AF9C), name: 'Open heart', unlocked: false),
    RewardBadge(icon: Icons.lock_outline, iconColor: Color(0xFFB8AF9C), name: 'Mountain', unlocked: false),
  ];
  final int badgesUnlocked = 4;
  final int badgesTotal = 12;

  final List<EarnTask> earnTasks = const [
    EarnTask(title: 'Daily check-in', subtitle: 'Pick a mood, anything.', points: 10, done: true),
    EarnTask(title: 'Complete an exercise', subtitle: 'Any breath or body scan.', points: 15, done: false),
    EarnTask(title: 'Journal an entry', subtitle: 'A few lines is enough.', points: 20, done: false),
  ];

  // ----- Wallet -----
  final int walletBalance = 2450;
  final String walletBalanceNote = '≈ 1 short session';

  final Map<String, dynamic> upcomingCharge = const {
    'therapistInitials': 'TM',
    'therapistColor': AppColors.moodStressed,
    'title': 'Session · Dr. Tariq',
    'subtitle': 'Fri, May 23 · 5:00 PM',
    'amount': 'Rs 4,500',
    'note': 'auto · Mastercard',
  };

  final List<PaymentMethod> paymentMethods = const [
    PaymentMethod(
      id: 'mc',
      name: 'Mastercard',
      lastFour: '3414',
      expiry: '09 / 27',
      isDefault: true,
      gradientColors: [Color(0xFF7A2E22), Color(0xFF4A1712)],
    ),
    PaymentMethod(
      id: 'ep',
      name: 'Easypaisa',
      lastFour: '7821',
      expiry: '09 / 27',
      isDefault: false,
      gradientColors: [Color(0xFF2C6E4A), Color(0xFF184630)],
    ),
  ];

  final List<WalletTransaction> transactions = const [
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
  ];

  /// Initiates a wallet top-up.
  ///
  /// NOTE: demo/placeholder only. Real implementation must go through
  /// a PCI-DSS compliant payment gateway (e.g. Stripe, or a licensed
  /// local processor) using their client-side tokenization SDK. The
  /// app must NEVER collect, transmit, or store raw card numbers or
  /// CVVs itself — only a token comes back from the gateway, which is
  /// what gets sent to your backend to charge the card.
  Future<void> topUp(int amount) async {
    await Future.delayed(const Duration(milliseconds: 400));
    notifyListeners();
  }

  // ----- Profile -----
  final String userName = 'Layla Siddiqui';
  final String joinedInfo = 'Joined Feb 2026 · Islamabad';
  final String therapistName = 'Dr. Tariq Mahmood';
  final String therapistSince = 'since Feb 2026';
  final String aidaPersonality = 'Gentle';
  final int pastSessionsCount = 8;
  final bool wearableConnected = true;
  final bool notificationsOn = true;
}