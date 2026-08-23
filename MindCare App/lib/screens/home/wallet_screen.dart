import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/app_feedback.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/wallet/balance_card.dart';
import '../../widgets/wallet/payment_method_card.dart';
import '../../widgets/wallet/transaction_tile.dart';
import '../../widgets/wallet/upcoming_charge_card.dart';

class WalletScreen extends StatelessWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 130),
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).maybePop(),
                      icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                    ),
                    const Expanded(
                      child: Text(
                        'WALLET',
                        textAlign: TextAlign.center,
                        style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                      ),
                    ),
                    IconButton(
                      onPressed: () => showComingSoon(context, 'Wallet settings'),
                      icon: const Icon(Icons.more_horiz, color: AppColors.textDark),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                BalanceCard(
                  balance: provider.walletBalance,
                  note: provider.walletBalanceNote,
                  onTopUp: () async {
                    await provider.topUp(5000);
                    if (context.mounted) showComingSoon(context, 'Top up (Rs 5,000)');
                  },
                  onWithdraw: () => showComingSoon(context, 'Withdraw funds'),
                  onHistory: () => showComingSoon(context, 'Full transaction history'),
                ),
                const SizedBox(height: 22),
                Text('UPCOMING CHARGE', style: AppTextStyles.label()),
                const SizedBox(height: 12),
                UpcomingChargeCard(charge: provider.upcomingCharge),
                const SizedBox(height: 22),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('PAYMENT METHODS', style: AppTextStyles.label()),
                    GestureDetector(
                      onTap: () => showComingSoon(context, 'Add payment method'),
                      child: const Text('+ Add', style: TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w700, fontSize: 13)),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 108,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: provider.paymentMethods.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 12),
                    itemBuilder: (context, index) => GestureDetector(
                      onTap: () => showComingSoon(context, '${provider.paymentMethods[index].name} details'),
                      child: PaymentMethodCard(method: provider.paymentMethods[index]),
                    ),
                  ),
                ),
                const SizedBox(height: 22),
                Text('RECENT', style: AppTextStyles.label()),
                const SizedBox(height: 8),
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
            const Positioned(right: 0, bottom: 24, child: SosButton()),
          ],
        ),
      ),
    );
  }
}