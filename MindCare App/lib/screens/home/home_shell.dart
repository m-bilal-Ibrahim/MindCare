import 'package:flutter/material.dart';
import '../../widgets/common/bottom_nav_bar.dart';
import '../../widgets/common/sos_button.dart';
import '../care/browse_therapists_screen.dart';
import 'circles_placeholder_screen.dart';
import 'home_screen.dart';
import 'me_placeholder_screen.dart';
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
    CirclesPlaceholderScreen(),
    MePlaceholderScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          IndexedStack(index: _index, children: _tabs),
          // Browse screen renders its own SOS button, so skip the
          // shell-level one on that tab to avoid a duplicate.
          if (_index != 1) const Positioned(right: 16, bottom: 78, child: SosButton()),
        ],
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
      ),
    );
  }
}