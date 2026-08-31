import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../main.dart';
import '../../models/community_data.dart';
import '../../providers/community_provider.dart';
import '../../widgets/circles/post_card.dart';
import '../../widgets/circles/post_options_sheet.dart';
import '../../widgets/common/sos_button.dart';
import 'create_post_screen.dart';

class CircleDetailScreen extends StatelessWidget {
  const CircleDetailScreen({super.key, required this.tag});
  final CircleTag tag;

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CommunityProvider>();
    final posts = provider.postsForCircle(tag.name);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 110),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Spacer(),
                    IconButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => MobileFrame(child: CreatePostScreen(initialCircle: tag.name))),
                      ),
                      icon: const Icon(Icons.add_circle_outline, color: AppColors.textDark),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Container(
                  height: 110,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(22),
                    gradient: LinearGradient(colors: tag.gradientColors, begin: Alignment.topLeft, end: Alignment.bottomRight),
                  ),
                  padding: const EdgeInsets.all(20),
                  alignment: Alignment.bottomLeft,
                  child: Text(tag.name, style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif')),
                ),
                const SizedBox(height: 10),
                Text('${tag.memberCount} members', style: AppTextStyles.body(size: 13)),
                const SizedBox(height: 20),
                Text('${posts.length} POSTS', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                if (posts.isEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 40),
                    child: Column(
                      children: [
                        const Icon(Icons.forum_outlined, size: 36, color: AppColors.textMuted),
                        const SizedBox(height: 12),
                        Text('No posts here yet. Be the first to share.', style: AppTextStyles.body()),
                      ],
                    ),
                  )
                else
                  ...posts.map(
                    (post) => PostCard(
                      post: post,
                      onMoreTap: () => showPostOptionsSheet(context, provider: context.read<CommunityProvider>(), post: post),
                    ),
                  ),
              ],
            ),
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}