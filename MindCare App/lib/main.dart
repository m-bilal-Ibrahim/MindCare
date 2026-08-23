import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'providers/onboarding_provider.dart';
import 'providers/checkin_provider.dart';
import 'providers/therapy_provider.dart';
import 'screens/onboarding/welcome_screen.dart';
import 'screens/home/home_shell.dart';

void main() {
  runApp(const MindCareApp());
}

class MindCareApp extends StatelessWidget {
  const MindCareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => OnboardingProvider()),
        ChangeNotifierProvider(create: (_) => CheckinProvider()),
        ChangeNotifierProvider(create: (_) => TherapyProvider()),
      ],
      child: MaterialApp(
        title: 'MindCare',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: const MobileFrame(child: WelcomeScreen()),
        onGenerateRoute: (settings) {
          if (settings.name == '/home') {
            return MaterialPageRoute(builder: (_) => const MobileFrame(child: HomeShell()));
          }
          return null;
        },
      ),
    );
  }
}

/// Constrains the app to a realistic phone width (max 430px, like an
/// iPhone Pro Max) whenever it's running somewhere wider — desktop
/// Chrome, Windows, macOS. On an actual phone screen, this has zero
/// effect since the screen is already narrower than the cap.
class MobileFrame extends StatelessWidget {
  const MobileFrame({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isWideScreen = screenWidth > 430;

    if (!isWideScreen) return child;

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      body: Center(
        child: Container(
          width: 430,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(28),
            boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 40, spreadRadius: 4)],
          ),
          child: child,
        ),
      ),
    );
  }
}