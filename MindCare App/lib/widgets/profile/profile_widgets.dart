import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../common/skeleton.dart';

/// Back button and a small centred caption.
class ProfileTopBar extends StatelessWidget {
  const ProfileTopBar({super.key, required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: () => Navigator.of(context).maybePop(),
          icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
        ),
        Expanded(
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
          ),
        ),
        const SizedBox(width: 48),
      ],
    );
  }
}

InputDecoration profileInputDecoration(String hint, {String? error}) => InputDecoration(
      hintText: hint,
      hintStyle: AppTextStyles.body(size: 15, color: AppColors.textLabel),
      errorText: error,
      errorMaxLines: 3,
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.border)),
      disabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.border)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.progressActive, width: 1.4)),
      errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.sos)),
      focusedErrorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.sos, width: 1.4)),
    );

class FieldLabel extends StatelessWidget {
  const FieldLabel(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(text, style: AppTextStyles.label()));
}

class FieldHint extends StatelessWidget {
  const FieldHint(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(top: 6), child: Text(text, style: AppTextStyles.body(size: 12)));
}

class FieldError extends StatelessWidget {
  const FieldError(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) =>
      Padding(padding: const EdgeInsets.only(top: 6, left: 4), child: Text(text, style: const TextStyle(color: AppColors.sos, fontSize: 12)));
}

/// A field that opens a picker (e.g. a date) instead of a keyboard.
class PickerField extends StatelessWidget {
  const PickerField({super.key, required this.text, required this.onTap, this.icon, this.placeholder = false, this.error});
  final String text;
  final VoidCallback onTap;
  final IconData? icon;
  final bool placeholder;
  final String? error;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          child: InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: onTap,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: error != null ? AppColors.sos : AppColors.border),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      text,
                      style: AppTextStyles.body(size: 15, color: placeholder ? AppColors.textLabel : AppColors.textDark),
                    ),
                  ),
                  if (icon != null) Icon(icon, size: 18, color: AppColors.textMuted),
                ],
              ),
            ),
          ),
        ),
        if (error != null) FieldError(error!),
      ],
    );
  }
}

class ChoicePill extends StatelessWidget {
  const ChoicePill({super.key, required this.label, required this.selected, required this.onTap});
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: selected ? AppColors.chipSelected : Colors.white,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: selected ? AppColors.chipSelected : AppColors.border),
          ),
          child: Text(
            label,
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: selected ? Colors.white : AppColors.textDark),
          ),
        ),
      ),
    );
  }
}

class DropdownField<T> extends StatelessWidget {
  const DropdownField({super.key, required this.value, required this.items, required this.labelOf, required this.onChanged, required this.hint, this.error});
  final T? value;
  final List<T> items;
  final String Function(T) labelOf;
  final ValueChanged<T?> onChanged;
  final String hint;
  final String? error;

  @override
  Widget build(BuildContext context) {
    // Keep a value that isn't in the (possibly still loading) list visible.
    final list = [if (value != null && !items.contains(value)) value as T, ...items];
    return DropdownButtonFormField<T>(
      initialValue: value,
      key: ValueKey('${value.hashCode}-${items.length}'),
      isExpanded: true,
      items: [for (final i in list) DropdownMenuItem<T>(value: i, child: Text(labelOf(i), overflow: TextOverflow.ellipsis))],
      onChanged: items.isEmpty ? null : onChanged,
      decoration: profileInputDecoration(hint, error: error),
      borderRadius: BorderRadius.circular(14),
      dropdownColor: Colors.white,
    );
  }
}

/// Round profile photo with initials when there's none. [busy] shimmers it
/// while an upload is in progress.
class ProfilePhoto extends StatelessWidget {
  const ProfilePhoto({super.key, required this.name, required this.photoUrl, this.size = 68, this.onTap, this.busy = false});
  final String name;
  final String? photoUrl;
  final double size;
  final VoidCallback? onTap;
  final bool busy;

  String get _initials {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final fallback = Container(
      color: const Color(0xFFE5382B),
      alignment: Alignment.center,
      child: Text(_initials, style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: size * 0.3)),
    );
    Widget photo = ClipOval(
      child: SizedBox(
        width: size,
        height: size,
        child: photoUrl == null
            ? fallback
            : Image.network(photoUrl!, fit: BoxFit.cover, errorBuilder: (_, __, ___) => fallback),
      ),
    );
    if (busy) {
      photo = Shimmer(child: SkeletonBox(height: size, circle: true));
    }
    if (onTap == null) return photo;
    return Semantics(
      button: true,
      label: 'Change profile photo',
      child: GestureDetector(
        onTap: busy ? null : onTap,
        child: Stack(
          children: [
            photo,
            Positioned(
              right: 0,
              bottom: 0,
              child: Container(
                width: size * 0.32,
                height: size * 0.32,
                decoration: BoxDecoration(color: AppColors.primaryDark, shape: BoxShape.circle, border: Border.all(color: AppColors.background, width: 2)),
                child: Icon(Icons.photo_camera_outlined, color: Colors.white, size: size * 0.16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ProfileErrorCard extends StatelessWidget {
  const ProfileErrorCard({super.key, required this.message, required this.sessionExpired, required this.onRetry});
  final String message;
  final bool sessionExpired;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(22)),
      child: Column(
        children: [
          Icon(sessionExpired ? Icons.lock_outline : Icons.cloud_off_outlined, color: AppColors.textMuted, size: 28),
          const SizedBox(height: 10),
          Text(sessionExpired ? 'Please sign in again' : "Couldn't load your profile", style: AppTextStyles.heading(size: 20)),
          const SizedBox(height: 6),
          Text(message, textAlign: TextAlign.center, style: AppTextStyles.body(size: 13)),
          const SizedBox(height: 14),
          OutlinedButton(
            onPressed: sessionExpired ? () => Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (_) => false) : onRetry,
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.border),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
            child: Text(sessionExpired ? 'Sign in' : 'Try again', style: const TextStyle(color: AppColors.textDark)),
          ),
        ],
      ),
    );
  }
}

/// Skeleton for the profile forms: photo, name, then labelled fields.
class ProfileFormSkeleton extends StatelessWidget {
  const ProfileFormSkeleton({super.key, this.fields = 5, this.withPhoto = true});
  final int fields;
  final bool withPhoto;

  @override
  Widget build(BuildContext context) {
    return Shimmer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (withPhoto) ...[
            const Center(child: SkeletonBox(height: 96, circle: true)),
            const SizedBox(height: 14),
            const Center(child: SkeletonBox(width: 160, height: 18)),
            const SizedBox(height: 26),
          ],
          for (var i = 0; i < fields; i++) ...[
            const SkeletonBox(width: 110, height: 10),
            const SizedBox(height: 10),
            const SkeletonBox(height: 50, radius: 14),
            const SizedBox(height: 20),
          ],
        ],
      ),
    );
  }
}
