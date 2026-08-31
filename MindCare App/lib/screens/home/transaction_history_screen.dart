import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/wallet/transaction_tile.dart';

class TransactionHistoryScreen extends StatelessWidget {
  const TransactionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 30),
          children: [
            Row(
              children: [
                IconButton(
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                ),
                const Expanded(
                  child: Text(
                    'ALL TRANSACTIONS',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('Your history.', style: AppTextStyles.heading(size: 28)),
            const SizedBox(height: 6),
            Text('${provider.transactions.length} transactions', style: AppTextStyles.body()),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
              child: Column(
                children: List.generate(provider.transactions.length, (i) {
                  return TransactionTile(transaction: provider.transactions[i], showDivider: i != provider.transactions.length - 1);
                }),
              ),
            ),
          ],
        ),
      ),
    );
  }
}