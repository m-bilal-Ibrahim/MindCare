import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/community_data.dart';
import '../models/hospital_data.dart';

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

  List<CommunityPost> _posts = [
    const CommunityPost(
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
    const CommunityPost(
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
    const CommunityPost(
      id: 'p3',
      authorName: 'Sana K.',
      handle: '@sana.k',
      avatarColor: Color(0xFFCBB36B),
      circleName: 'New parents',
      timeAgo: '8h',
      content: "3 AM feed, and for once I wasn't dreading it. Small thing, but I noticed it.",
      hearts: 31,
      hugs: 12,
      comments: 4,
    ),
  ];

  final Set<String> _hiddenPostIds = {};
  final Set<String> _blockedHandles = {};
  final Set<String> _reportedPostIds = {};

  List<CommunityPost> get visiblePosts =>
      _posts.where((p) => !_hiddenPostIds.contains(p.id) && !_blockedHandles.contains(p.handle)).toList();

  List<CommunityPost> get posts => visiblePosts;

  List<CommunityPost> postsForCircle(String circleName) =>
      visiblePosts.where((p) => p.circleName == circleName).toList();

  int postCountForCircle(String circleName) => postsForCircle(circleName).length;

  void createPost({required String circleName, required String content}) {
    final trimmed = content.trim();
    if (trimmed.isEmpty) return;

    final newPost = CommunityPost(
      id: 'p_${DateTime.now().millisecondsSinceEpoch}',
      authorName: 'Anonymous',
      handle: '@you',
      avatarColor: AppColors.progressActive,
      circleName: circleName,
      timeAgo: 'now',
      content: trimmed,
      hearts: 0,
      hugs: 0,
      comments: 0,
      isAnonymous: true,
    );

    _posts = [newPost, ..._posts];
    notifyListeners();
  }

  void reportPost(String postId) {
    _reportedPostIds.add(postId);
    notifyListeners();
  }

  bool isReported(String postId) => _reportedPostIds.contains(postId);

  void hidePost(String postId) {
    _hiddenPostIds.add(postId);
    notifyListeners();
  }

  void blockUser(String handle) {
    _blockedHandles.add(handle);
    notifyListeners();
  }

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

   final List<Hospital> nearbyHospitals = const [
    Hospital(name: 'Shifa International Hospital', address: 'Pitras Bukhari Rd, H-8/4, Islamabad', distanceKm: 1.8, isOpen24h: true, phoneNumber: '+925184444'),
    Hospital(name: 'Quaid-e-Azam International Hospital', address: 'Rawal Rd, Chak Shahzad, Islamabad', distanceKm: 3.2, isOpen24h: true, phoneNumber: '+92519106666'),
    Hospital(name: 'KRL Hospital', address: 'G-9/4, Islamabad', distanceKm: 4.5, isOpen24h: false, phoneNumber: '+925191051190'),
  ];
}