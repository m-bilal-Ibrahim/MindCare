import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

/// Calm time today, worked out from sensor readings. Shows an empty
/// state when there are no readings today.
class CalmTimeRingCard extends StatelessWidget {
  const CalmTimeRingCard({super.key, required this.calmToday});
  final ({Duration calm, double share})? calmToday;

  String _duration(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes % 60;
    if (h == 0) return '${m}m today';
    return '${h}h ${m}m today';
  }

  @override
  Widget build(BuildContext context) {
    final data = calmToday;
    final percent = data?.share ?? 0;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: const Color(0xFFDCEAE2), borderRadius: BorderRadius.circular(20)),
      child: Row(
        children: [
          SizedBox(
            width: 64,
            height: 64,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CustomPaint(size: const Size(64, 64), painter: _RingPainter(percent)),
                Text(
                  data == null ? '—' : '${(percent * 100).round()}%',
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: AppColors.textDark),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('CALM TIME', style: AppTextStyles.label()),
                const SizedBox(height: 4),
                Text(data == null ? 'No readings today' : _duration(data.calm), style: AppTextStyles.heading(size: 20)),
                const SizedBox(height: 4),
                Text(
                  data == null
                      ? 'Appears once your sensor shares heart rate and breathing.'
                      : 'Sensor-detected · steady heart rate & breath',
                  style: AppTextStyles.body(size: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  _RingPainter(this.percent);
  final double percent;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;

    final trackPaint = Paint()
      ..color = AppColors.progressTrack
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(center, radius, trackPaint);

    if (percent <= 0) return;
    final progressPaint = Paint()
      ..color = AppColors.progressActive
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), -1.5708, 6.2832 * percent, false, progressPaint);
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) => oldDelegate.percent != percent;
}
