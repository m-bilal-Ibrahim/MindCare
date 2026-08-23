import 'package:flutter/material.dart';

class MotivationTabBar extends StatelessWidget {
  const MotivationTabBar({super.key, required this.tabs, required this.selected, required this.onChanged});
  final List<String> tabs;
  final String selected;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.1), borderRadius: BorderRadius.circular(16)),
      child: Row(
        children: tabs.map((tab) {
          final isSelected = tab == selected;
          return Expanded(
            child: GestureDetector(
              onTap: () => onChanged(tab),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: isSelected ? Colors.white.withOpacity(0.18) : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                ),
                alignment: Alignment.center,
                child: Text(
                  tab,
                  style: TextStyle(color: Colors.white, fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500, fontSize: 14),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}