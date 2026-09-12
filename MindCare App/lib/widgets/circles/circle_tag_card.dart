import 'package:flutter/material.dart';
import '../../models/community_data.dart';

class CircleTagCard extends StatelessWidget {
  const CircleTagCard({super.key, required this.tag, this.onTap});
  final CircleTag tag;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 110,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 110,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: LinearGradient(colors: tag.gradientColors, begin: Alignment.topLeft, end: Alignment.bottomRight),
              ),
            ),
            const SizedBox(height: 8),
            Text(tag.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            Text(tag.memberCount, style: const TextStyle(fontSize: 12, color: Color(0xFF7A7A70))),
          ],
        ),
      ),
    );
  }
}