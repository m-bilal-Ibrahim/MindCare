import 'package:flutter/material.dart';
import '../../widgets/common/bottom_nav_bar.dart';
import '../../widgets/common/sos_button.dart';
import '../care/browse_therapists_screen.dart';
import 'circles_screen.dart';
import 'home_screen.dart';
import 'profile_screen.dart';
import 'pulse_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  static const _tabs = [
    HomeScreen(),
    BrowseTherapistsScreen(),
    PulseScreen(),
    CirclesScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          IndexedStack(index: _index, children: _tabs),
          // Browse, Circles, and Profile screens each render their own
          // SOS button in their scrollable content, so skip the
          // shell-level one on those tabs to avoid a duplicate.
          if (_index != 1 && _index != 3 && _index != 4) const Positioned(right: 16, bottom: 78, child: SosButton()),
        ],
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
      ),
    );
  }
}