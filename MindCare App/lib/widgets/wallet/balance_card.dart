import 'package:flutter/material.dart';
import '../../core/theme/app_text_styles.dart';

class BalanceCard extends StatelessWidget {
  const BalanceCard({
    super.key,
    required this.balance,
    required this.note,
    required this.onTopUp,
    required this.onWithdraw,
    required this.onHistory,
  });

  final int balance;
  final String note;
  final VoidCallback onTopUp;
  final VoidCallback onWithdraw;
  final VoidCallback onHistory;

  String _formatAmount(int value) {
    final s = value.toString();
    final buffer = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i != 0 && (s.length - i) % 3 == 0) buffer.write(',');
      buffer.write(s[i]);
    }
    return buffer.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF2B453C), Color(0xFF162622)], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('MINDCARE BALANCE', style: TextStyle(color: Colors.white60, letterSpacing: 1, fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              const Text('Rs ', style: TextStyle(color: Colors.white70, fontSize: 20)),
              Text(_formatAmount(balance), style: const TextStyle(color: Colors.white, fontSize: 40, fontFamily: 'serif')),
            ],
          ),
          const SizedBox(height: 4),
          Text(note, style: const TextStyle(color: Colors.white54, fontSize: 13)),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(child: _ActionButton(icon: Icons.add, label: 'Top up', onTap: onTopUp)),
              const SizedBox(width: 10),
              Expanded(child: _ActionButton(icon: Icons.arrow_upward, label: 'Withdraw', onTap: onWithdraw)),
              const SizedBox(width: 10),
              Expanded(child: _ActionButton(icon: Icons.history, label: 'History', onTap: onHistory)),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.12), borderRadius: BorderRadius.circular(14)),
        child: Column(
          children: [
            Icon(icon, color: Colors.white, size: 16),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}