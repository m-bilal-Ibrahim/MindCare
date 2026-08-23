import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class SosButton extends StatelessWidget {
  const SosButton({super.key, this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap ?? () => _showSosSheet(context),
      child: Container(
        width: 64,
        height: 64,
        decoration: const BoxDecoration(
          color: AppColors.sos,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(color: Colors.black26, blurRadius: 10, offset: Offset(0, 4)),
          ],
        ),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('SOS', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
            Text('GET HELP', style: TextStyle(color: Colors.white, fontSize: 7, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  void _showSosSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Need immediate help?', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              const Text('If you are in danger or crisis, contact your local emergency number right now.'),
            ],
          ),
        ),
      ),
    );
  }
}