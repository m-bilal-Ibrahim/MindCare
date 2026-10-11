import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/community_data.dart';
import '../models/hospital_data.dart';

class CommunityProvider extends ChangeNotifier {
  // ----- Circles feed -----
  // The circle topics are part of the app's design; member counts and
  // posts come from the backend, so they start empty.
  List<CircleTag> circleTags = const [
    CircleTag(name: 'Anxiety', gradientColors: [Color(0xFFD98B7A), Color(0xFFB85E4E)]),
    CircleTag(name: 'New parents', gradientColors: [Color(0xFFCBB36B), Color(0xFFA88E45)]),
    CircleTag(name: 'Sober walk', gradientColors: [Color(0xFF3FA79A), Color(0xFF1F6E63)]),
    CircleTag(name: 'After loss', gradientColors: [Color(0xFF8B90D9), Color(0xFF5C61B0)]),
  ];

  void setCircleTags(List<CircleTag> tags) {
    circleTags = tags;
    notifyListeners();
  }

  static const List<String> feedFilters = ['Today', 'Anxiety', 'Wins'];
  String selectedFeedFilter = 'Today';

  void setFeedFilter(String filter) {
    selectedFeedFilter = filter;
    notifyListeners();
  }

  List<CommunityPost> _posts = const [];

  void setPosts(List<CommunityPost> posts) {
    _posts = posts;
    notifyListeners();
  }

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
  String? selectedFeeling;

  void selectFeeling(String feeling) {
    selectedFeeling = feeling;
    notifyListeners();
  }

  static const List<String> topicOptions = [
    'Anxiety', 'Loneliness', 'Family', 'Work', 'Relationship', 'Grief', 'Faith', 'Other',
  ];
  Set<String> selectedTopics = {};

  void toggleTopic(String topic) {
    if (selectedTopics.contains(topic)) {
      selectedTopics.remove(topic);
    } else {
      selectedTopics.add(topic);
    }
    notifyListeners();
  }

  String noteText = '';
  void setNoteText(String text) => noteText = text;

  bool postingRequest = false;

  Future<void> postPeerTalkRequest() async {
    postingRequest = true;
    notifyListeners();
    // The backend request that matches a peer listener goes here.
    await Future.delayed(const Duration(milliseconds: 300));
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
      subtitle: 'A slow, gentle conversation while you wait for help.',
    ),
    SosResource(
      icon: Icons.groups,
      iconBackground: Color(0xFF4A7A67),
      title: 'Notify your circle',
      subtitle: 'People you trust get a gentle ping.',
    ),
    SosResource(
      icon: Icons.local_hospital,
      iconBackground: AppColors.textDark,
      title: 'Nearby hospitals',
      subtitle: 'Hospitals near you, closest first.',
    ),
  ];

  /// Hospitals near the patient's location, closest first, from the backend.
  List<Hospital> nearbyHospitals = const [];

  void setNearbyHospitals(List<Hospital> hospitals) {
    nearbyHospitals = hospitals;
    notifyListeners();
  }
}
