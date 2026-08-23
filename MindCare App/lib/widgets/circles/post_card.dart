import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/community_data.dart';

class PostCard extends StatelessWidget {
  const PostCard({super.key, required this.post, this.onMoreTap});
  final CommunityPost post;
  final VoidCallback? onMoreTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: post.avatarColor,
                child: Text(post.authorName.substring(0, 1), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(post.authorName, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark, fontSize: 14)),
                        Text(' · ${post.handle}', style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
                      ],
                    ),
                    Row(
                      children: [
                        const Text('in ', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                        Text(post.circleName, style: const TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w600, fontSize: 12)),
                        Text(' · ${post.timeAgo}', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                      ],
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: onMoreTap,
                child: const Padding(
                  padding: EdgeInsets.all(4),
                  child: Icon(Icons.more_horiz, color: AppColors.textMuted, size: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(post.content, style: const TextStyle(color: AppColors.textDark, fontSize: 14, height: 1.4)),
          const SizedBox(height: 14),
          Row(
            children: [
              _ReactionCount(icon: Icons.favorite_border, count: post.hearts),
              const SizedBox(width: 18),
              _ReactionCount(icon: Icons.front_hand_outlined, count: post.hugs),
              const SizedBox(width: 18),
              _ReactionCount(icon: Icons.chat_bubble_outline, count: post.comments),
            ],
          ),
        ],
      ),
    );
  }
}

class _ReactionCount extends StatelessWidget {
  const _ReactionCount({required this.icon, required this.count});
  final IconData icon;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: AppColors.textMuted),
        const SizedBox(width: 5),
        Text('$count', style: const TextStyle(fontSize: 13, color: AppColors.textMuted)),
      ],
    );
  }
}