import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/app_feedback.dart';
import '../../main.dart';
import '../../providers/community_provider.dart';
import '../../widgets/circles/circle_tag_card.dart';
import '../../widgets/circles/post_card.dart';
import '../sos/peer_talk_screen.dart';

class CirclesScreen extends StatelessWidget {
  const CirclesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CommunityProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 110),
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('CIRCLES', style: AppTextStyles.label()),
                      const SizedBox(height: 6),
                      Text("You're not alone in it.", style: AppTextStyles.heading(size: 26)),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: () => showComingSoon(context, 'Create a post'),
                  child: Container(
                    width: 42,
                    height: 42,
                    decoration: const BoxDecoration(color: AppColors.textDark, shape: BoxShape.circle),
                    child: const Icon(Icons.add, color: Colors.white, size: 20),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            GestureDetector(
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MobileFrame(child: PeerTalkScreen())),
              ),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(20)),
                child: Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(color: AppColors.infoBoxText, borderRadius: BorderRadius.circular(14)),
                      child: const Icon(Icons.graphic_eq, color: Colors.white, size: 20),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Need to talk to someone?', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.infoBoxText)),
                          const SizedBox(height: 3),
                          Text('Post an anonymous note. One listener accepts · voices are masked.', style: TextStyle(fontSize: 12, color: AppColors.infoBoxText.withOpacity(0.85))),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: AppColors.infoBoxText),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 166,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: provider.circleTags.length,
                separatorBuilder: (_, __) => const SizedBox(width: 14),
                itemBuilder: (context, index) {
                  final tag = provider.circleTags[index];
                  return CircleTagCard(
                    tag: tag,
                    onTap: () => showComingSoon(context, '${tag.name} circle'),
                  );
                },
              ),
            ),
            const SizedBox(height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('RECENT POSTS', style: AppTextStyles.label()),
                Row(
                  children: CommunityProvider.feedFilters.map((filter) {
                    final selected = provider.selectedFeedFilter == filter;
                    return Padding(
                      padding: const EdgeInsets.only(left: 6),
                      child: GestureDetector(
                        onTap: () => context.read<CommunityProvider>().setFeedFilter(filter),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: selected ? AppColors.chipSelected : AppColors.chipUnselected,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(filter, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: selected ? Colors.white : AppColors.chipTextUnselected)),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ...provider.posts.map(
              (post) => PostCard(
                post: post,
                onMoreTap: () => showComingSoon(context, 'Post options'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}