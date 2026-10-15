import 'package:flutter/material.dart';

/// Skeleton loading: grey placeholder shapes in the layout of the content
/// that is on its way, with a soft light sweeping across them.
///
/// Wrap a group of [SkeletonBox]es in one [Shimmer] so they shine together.
class Shimmer extends StatefulWidget {
  const Shimmer({super.key, required this.child, this.base, this.highlight});

  final Widget child;

  /// Placeholder colour and the sweep's highlight. Defaults suit the light
  /// cream screens; pass lighter-on-dark colours for dark screens.
  final Color? base;
  final Color? highlight;

  /// Colours for the dark Motivation screens.
  static const darkBase = Color(0x1FFFFFFF);
  static const darkHighlight = Color(0x40FFFFFF);

  @override
  State<Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final base = widget.base ?? const Color(0xFFE6DFCF);
    final highlight = widget.highlight ?? const Color(0xFFF6F1E6);
    return Semantics(
      label: 'Loading',
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          final t = _controller.value;
          return ShaderMask(
            blendMode: BlendMode.srcATop,
            shaderCallback: (bounds) => LinearGradient(
              begin: Alignment(-1.0 + 3 * t - 1, -0.2),
              end: Alignment(1.0 + 3 * t - 1, 0.2),
              colors: [base, highlight, base],
              stops: const [0.35, 0.5, 0.65],
            ).createShader(bounds),
            child: child,
          );
        },
        child: _SkeletonColor(color: base, child: widget.child),
      ),
    );
  }
}

/// Passes the placeholder colour down to [SkeletonBox]es.
class _SkeletonColor extends InheritedWidget {
  const _SkeletonColor({required this.color, required super.child});
  final Color color;

  @override
  bool updateShouldNotify(_SkeletonColor old) => old.color != color;
}

/// One placeholder shape. Leave [width] null to fill the available width.
class SkeletonBox extends StatelessWidget {
  const SkeletonBox({super.key, this.width, required this.height, this.radius = 8, this.circle = false});

  final double? width;
  final double height;
  final double radius;
  final bool circle;

  @override
  Widget build(BuildContext context) {
    final color = context.dependOnInheritedWidgetOfExactType<_SkeletonColor>()?.color ?? const Color(0xFFE6DFCF);
    return Container(
      width: circle ? height : width,
      height: height,
      decoration: BoxDecoration(
        color: color,
        shape: circle ? BoxShape.circle : BoxShape.rectangle,
        borderRadius: circle ? null : BorderRadius.circular(radius),
      ),
    );
  }
}

/// A short stack of text lines, the last one shorter, like a paragraph.
class SkeletonLines extends StatelessWidget {
  const SkeletonLines({super.key, this.lines = 2, this.lineHeight = 12, this.gap = 8, this.lastWidthFactor = 0.6, this.alignEnd = false, this.center = false});

  final int lines;
  final double lineHeight;
  final double gap;
  final double lastWidthFactor;
  final bool alignEnd;
  final bool center;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) => Column(
        crossAxisAlignment: center
            ? CrossAxisAlignment.center
            : alignEnd
                ? CrossAxisAlignment.end
                : CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < lines; i++) ...[
            if (i > 0) SizedBox(height: gap),
            SkeletonBox(width: i == lines - 1 && lines > 1 ? c.maxWidth * lastWidthFactor : c.maxWidth, height: lineHeight, radius: lineHeight / 2),
          ],
        ],
      ),
    );
  }
}
