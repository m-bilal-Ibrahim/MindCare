import 'package:flutter/material.dart';
import '../../main.dart';
import '../../screens/sos/sos_screen.dart';

class SosButton extends StatelessWidget {
  const SosButton({super.key, this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap ?? () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const MobileFrame(child: SosScreen())),
      ),
      child: Container(
        width: 64,
        height: 64,
        decoration: const BoxDecoration(
          color: Color(0xFFD8664B),
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
}