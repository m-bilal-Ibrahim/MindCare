import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

class AppTextStyles {
  AppTextStyles._();

  static TextStyle heading({double size = 32, FontStyle style = FontStyle.normal}) {
    return GoogleFonts.playfairDisplay(
      fontSize: size,
      fontStyle: style,
      color: AppColors.textDark,
      height: 1.15,
      fontWeight: FontWeight.w500,
    );
  }

  static TextStyle body({double size = 15, Color? color, FontWeight weight = FontWeight.normal}) {
    return GoogleFonts.inter(
      fontSize: size,
      color: color ?? AppColors.textMuted,
      fontWeight: weight,
      height: 1.4,
    );
  }

  static TextStyle label() => GoogleFonts.inter(
        fontSize: 12,
        letterSpacing: 1.0,
        fontWeight: FontWeight.w600,
        color: AppColors.textLabel,
      );

  static TextStyle button() => GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: Colors.white,
      );
}