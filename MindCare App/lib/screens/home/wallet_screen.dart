import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/share_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/wallet/balance_card.dart';
import '../../widgets/wallet/payment_method_card.dart';
import '../../widgets/wallet/transaction_tile.dart';
import '../../widgets/wallet/upcoming_charge_card.dart';
import 'add_payment_method_screen.dart';
import 'transaction_history_screen.dart';

class WalletScreen extends StatelessWidget {
  const WalletScreen({super.key});

  void _showWalletSettings(BuildContext context) {
    final provider = context.read<AccountProvider>();
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        return SafeArea(
          child: StatefulBuilder(
            builder: (sheetContext, setSheetState) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SwitchListTile(
                      title: const Text(
                        'Auto-renewal',
                        style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark),
                      ),
                      subtitle: const Text(
                        'Automatically renew your plan each cycle.',
                        style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                      ),
                      value: provider.autoRenewEnabled,
                      activeThumbColor: AppColors.primaryDark,
                      onChanged: (value) {
                        provider.setAutoRenew(value);
                        setSheetState(() {});
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.description_outlined, color: AppColors.textDark),
                      title: const Text(
                        'Download statement',
                        style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark),
                      ),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        if (provider.transactions.isEmpty) {
                          ScaffoldMessenger.of(context)
                              .showSnackBar(const SnackBar(content: Text('No transactions yet, so there is no statement to download.')));
                          return;
                        }
                        final summary = provider.transactions.take(5).map((t) => '${t.title}: ${t.amount}').join('\n');
                        ShareService.instance.shareText(
                          'MindCare wallet statement\nBalance: Rs ${provider.walletBalance ?? 0}\n\n$summary',
                          subject: 'MindCare wallet statement',
                        );
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.attach_money, color: AppColors.textDark),
                      title: const Text(
                        'Currency',
                        style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark),
                      ),
                      trailing: const Text(
                        'PKR',
                        style: TextStyle(color: AppColors.textMuted, fontWeight: FontWeight.w600),
                      ),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('MindCare currently only supports PKR.')));
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  void _showPaymentMethodOptions(BuildContext context, String id, bool isDefault) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (!isDefault)
                  ListTile(
                    leading: const Icon(Icons.check_circle_outline, color: AppColors.textDark),
                    title: const Text(
                      'Set as default',
                      style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark),
                    ),
                    onTap: () {
                      context.read<AccountProvider>().setDefaultPaymentMethod(id);
                      Navigator.of(sheetContext).pop();
                    },
                  ),
                ListTile(
                  leading: const Icon(Icons.delete_outline, color: AppColors.sos),
                  title: const Text(
                    'Remove card',
                    style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.sos),
                  ),
                  onTap: () {
                    context.read<AccountProvider>().removePaymentMethod(id);
                    Navigator.of(sheetContext).pop();
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();
    final recentTransactions = provider.transactions.take(3).toList();

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
                      onPressed: () => _showWalletSettings(context),
                      icon: const Icon(Icons.more_horiz, color: AppColors.textDark),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                BalanceCard(
                  balance: provider.walletBalance,
                  note: null,
                  // Moving money needs the payment gateway; until it exists we say so rather than fake a balance.
                  onTopUp: () =>
                      ScaffoldMessenger.of(context)
                          .showSnackBar(const SnackBar(content: Text('Top-ups open once payments are connected.'))),
                  onWithdraw: () =>
                      ScaffoldMessenger.of(context)
                          .showSnackBar(const SnackBar(content: Text('Withdrawals open once payments are connected.'))),
                  onHistory: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TransactionHistoryScreen())),
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
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AddPaymentMethodScreen())),
                      child: const Text(
                        '+ Add',
                        style: TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                if (provider.paymentMethods.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                    child: Row(
                      children: [
                        const Icon(Icons.credit_card_off_outlined, size: 20, color: AppColors.textMuted),
                        const SizedBox(width: 12),
                        Expanded(child: Text('No saved cards yet.', style: AppTextStyles.body(size: 13))),
                      ],
                    ),
                  )
                else
                  SizedBox(
                    height: 108,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: provider.paymentMethods.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 12),
                      itemBuilder: (context, index) {
                        final method = provider.paymentMethods[index];
                        return GestureDetector(
                          onTap: () => _showPaymentMethodOptions(context, method.id, method.isDefault),
                          child: PaymentMethodCard(method: method),
                        );
                      },
                    ),
                  ),
                const SizedBox(height: 22),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('RECENT', style: AppTextStyles.label()),
                    GestureDetector(
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TransactionHistoryScreen())),
                      child: const Text(
                        'see all',
                        style: TextStyle(color: AppColors.progressActive, fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                  child: recentTransactions.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 4),
                          child: Row(
                            children: [
                              const Icon(Icons.receipt_long_outlined, size: 20, color: AppColors.textMuted),
                              const SizedBox(width: 12),
                              Expanded(child: Text('No transactions yet.', style: AppTextStyles.body(size: 13))),
                            ],
                          ),
                        )
                      : Column(
                          children: List.generate(recentTransactions.length, (i) {
                            return TransactionTile(transaction: recentTransactions[i], showDivider: i != recentTransactions.length - 1);
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
