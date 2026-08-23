import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/community_data.dart';

class CommunityProvider extends ChangeNotifier {
  // ----- Circles feed -----
  final List<CircleTag> circleTags = const [
    CircleTag(name: 'Anxiety', memberCount: '1.2k', gradientColors: [Color(0xFFD98B7A), Color(0xFFB85E4E)]),
    CircleTag(name: 'New parents', memberCount: '480', gradientColors: [Color(0xFFCBB36B), Color(0xFFA88E45)]),
    CircleTag(name: 'Sober walk', memberCount: '230', gradientColors: [Color(0xFF3FA79A), Color(0xFF1F6E63)]),
    CircleTag(name: 'After loss', memberCount: '75', gradientColors: [Color(0xFF8B90D9), Color(0xFF5C61B0)]),
  ];

  static const List<String> feedFilters = ['Today', 'Anxiety', 'Wins'];
  String selectedFeedFilter = 'Today';

  void setFeedFilter(String filter) {
    selectedFeedFilter = filter;
    notifyListeners();
  }

  final List<CommunityPost> posts = const [
    CommunityPost(
      id: 'p1',
      authorName: 'Anonymous',
      handle: '@warm-thistle',
      avatarColor: Color(0xFF6FBE3E),
      circleName: 'Anxiety',
      timeAgo: '2h',
      content: 'Made it through the meeting without spiraling. Sat with the racing heart instead of fighting it. Tiny win, but I\'ll take it.',
      hearts: 47,
      hugs: 22,
      comments: 8,
      isAnonymous: true,
    ),
    CommunityPost(
      id: 'p2',
      authorName: 'Ammar S.',
      handle: '@ammar.s',
      avatarColor: Color(0xFF2497D9),
      circleName: 'Sober walk',
      timeAgo: '5h',
      content: 'Day 90. The walks really do help. If anyone in Islamabad wants company tomorrow morning, drop a 🌿.',
      hearts: 63,
      hugs: 19,
      comments: 14,
    ),
  ];

  // ----- Peer talk request -----
  static const List<String> feelingOptions = ['Lonely', 'Anxious', 'Low', 'Overwhelmed'];
  String? selectedFeeling = 'Anxious';

  void selectFeeling(String feeling) {
    selectedFeeling = feeling;
    notifyListeners();
  }

  static const List<String> topicOptions = [
    'Anxiety', 'Loneliness', 'Family', 'Work', 'Relationship', 'Grief', 'Faith', 'Other',
  ];
  Set<String> selectedTopics = {'Anxiety'};

  void toggleTopic(String topic) {
    if (selectedTopics.contains(topic)) {
      selectedTopics.remove(topic);
    } else {
      selectedTopics.add(topic);
    }
    notifyListeners();
  }

  String noteText = "Just had a rough morning. Don't need advice, just a kind voice for a few minutes.";
  void setNoteText(String text) => noteText = text;

  bool postingRequest = false;

  /// Posts an anonymous peer-talk request to the backend matching queue.
  ///
  /// NOTE: demo/placeholder only. In production, this must go through
  /// an authenticated HTTPS call. The note text and mood selection are
  /// sensitive personal-support content — the backend must never log
  /// this in plaintext analytics, and the eventual voice call must use
  /// a masked/pitch-shifted audio pipeline server-side so raw voice
  /// data isn't exposed to the peer listener, matching the "voices
  /// are softly masked" promise shown in the UI.
  Future<void> postPeerTalkRequest() async {
    postingRequest = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 900));
    postingRequest = false;
    notifyListeners();
  }

  // ----- SOS -----
  final List<SosResource> sosResources = const [
    SosResource(
      icon: Icons.call,
      iconBackground: AppColors.sos,
      title: 'Umang helpline · 0311-7786264',
      subtitle: 'Trained listeners, in Urdu or English. Free.',
    ),
    SosResource(
      icon: Icons.auto_awesome,
      iconBackground: AppColors.primaryDark,
      title: 'Talk to Aida, with crisis mode',
      subtitle: 'Slow conversation. She can stay as long as you need.',
    ),
    SosResource(
      icon: Icons.groups,
      iconBackground: Color(0xFF4A7A67),
      title: 'Notify your circle',
      subtitle: "Ammi, Hira, Zoya · they'll get a gentle ping.",
    ),
    SosResource(
      icon: Icons.local_hospital,
      iconBackground: AppColors.textDark,
      title: 'Nearby hospitals',
      subtitle: '3 within 5 km · Shifa, Quaid-e-Azam, KRL',
    ),
  ];
}