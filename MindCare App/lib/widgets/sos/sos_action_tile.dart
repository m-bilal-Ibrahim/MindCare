import 'package:flutter/material.dart';
import '../../models/community_data.dart';

class SosActionTile extends StatelessWidget {
  const SosActionTile({super.key, required this.resource, this.onTap});
  final SosResource resource;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(color: resource.iconBackground, borderRadius: BorderRadius.circular(12)),
              child: Icon(resource.icon, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(resource.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: Color(0xFF3A2620))),
                  const SizedBox(height: 3),
                  Text(resource.subtitle, style: const TextStyle(fontSize: 12, color: Color(0xFF8A6D65)), maxLines: 2, overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Color(0xFF8A6D65)),
          ],
        ),
      ),
    );
  }
}