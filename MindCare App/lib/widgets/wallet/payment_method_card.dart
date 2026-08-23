import 'package:flutter/material.dart';
import '../../models/account_data.dart';

class PaymentMethodCard extends StatelessWidget {
  const PaymentMethodCard({super.key, required this.method});
  final PaymentMethod method;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 168,
      height: 108,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: method.gradientColors, begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(method.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              if (method.isDefault)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(10)),
                  child: const Text('DEFAULT', style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.w700)),
                ),
            ],
          ),
          const Spacer(),
          Text('•••• ${method.lastFour}', style: const TextStyle(color: Colors.white, fontSize: 15, letterSpacing: 1)),
          const SizedBox(height: 4),
          Text('Expires ${method.expiry}', style: const TextStyle(color: Colors.white60, fontSize: 11)),
        ],
      ),
    );
  }
}