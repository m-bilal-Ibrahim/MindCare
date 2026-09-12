import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/account_data.dart';

class TransactionTile extends StatelessWidget {
  const TransactionTile({super.key, required this.transaction, this.showDivider = true});
  final WalletTransaction transaction;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(color: transaction.iconBackground, borderRadius: BorderRadius.circular(11)),
                child: Icon(transaction.icon, size: 17, color: AppColors.textDark),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(transaction.title, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textDark, fontSize: 14)),
                    const SizedBox(height: 2),
                    Text(transaction.subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                  ],
                ),
              ),
              Text(
                transaction.amount,
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: transaction.isCredit ? AppColors.progressActive : AppColors.textDark),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1, color: AppColors.border),
      ],
    );
  }
}