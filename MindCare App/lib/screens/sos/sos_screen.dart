import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/utils/app_feedback.dart';
import '../../main.dart';
import '../../providers/community_provider.dart';
import '../../widgets/sos/sos_action_tile.dart';
import '../home/aida_chat_screen.dart';
import 'nearby_hospitals_screen.dart';
import 'notify_circle_screen.dart';

class SosScreen extends StatelessWidget {
  const SosScreen({super.key});

  /// Opens the phone's own dialer, pre-filled with the helpline
  /// number. MindCare never places the call itself — this hands off
  /// to the OS dialer, which is the safe, standard approach for a
  /// crisis line: the person can see the number, confirm, and place
  /// the call through their normal phone app.
  Future<void> _callHelpline(BuildContext context, String number) async {
    final uri = Uri(scheme: 'tel', path: number);
    final launched = await launchUrl(uri);
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Couldn't open the dialer. Call $number directly.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CommunityProvider>();
    final resources = provider.sosResources;

    return Scaffold(
      backgroundColor: const Color(0xFFF7DCD6),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.of(context).maybePop(),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: const Icon(Icons.close, size: 18, color: Color(0xFF3A2620)),
                  ),
                ),
                const Expanded(
                  child: Text(
                    'YOU ARE SAFE HERE',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: Color(0xFFB35440), fontWeight: FontWeight.w700, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 40),
              ],
            ),
            const SizedBox(height: 24),
            const Text.rich(
              TextSpan(
                style: TextStyle(color: Color(0xFFB0503C), fontSize: 30, fontFamily: 'serif', height: 1.25),
                children: [
                  TextSpan(text: "We're with you,\n"),
                  TextSpan(text: 'right now.', style: TextStyle(fontStyle: FontStyle.italic, color: Color(0xFFB0503C))),
                ],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 14),
            const Text(
              'Pick what feels right. We can also do nothing for a minute and breathe together.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFFC17A63), fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 34),
            Center(
              child: GestureDetector(
                onTap: () => _callHelpline(context, '03117786264'),
                child: Container(
                  width: 220,
                  height: 220,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFFF0C3B8).withOpacity(0.5)),
                  child: Center(
                    child: Container(
                      width: 180,
                      height: 180,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(colors: [Color(0xFFC96A50), Color(0xFFAD4C36)]),
                      ),
                      child: const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Call a person', style: TextStyle(color: Colors.white, fontSize: 20, fontFamily: 'serif')),
                          SizedBox(height: 8),
                          Text('TAP TO CALL', style: TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 36),
            SosActionTile(
              resource: resources[0],
              onTap: () => _callHelpline(context, '03117786264'),
            ),
            SosActionTile(
              resource: resources[1],
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MobileFrame(child: AidaChatScreen())),
              ),
            ),
            SosActionTile(
              resource: resources[2],
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MobileFrame(child: NotifyCircleScreen())),
              ),
            ),
            SosActionTile(
              resource: resources[3],
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MobileFrame(child: NearbyHospitalsScreen())),
              ),
            ),
          ],
        ),
      ),
    );
  }
}