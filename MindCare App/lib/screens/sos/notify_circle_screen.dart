import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/account_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/sos/circle_contact_tile.dart';

class NotifyCircleScreen extends StatefulWidget {
  const NotifyCircleScreen({super.key});

  @override
  State<NotifyCircleScreen> createState() => _NotifyCircleScreenState();
}

class _NotifyCircleScreenState extends State<NotifyCircleScreen> {
  final Set<String> _selected = {};
  bool _sending = false;
  bool _sent = false;

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccountProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFFF7DCD6),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: ListView(
            children: [
              const SizedBox(height: 8),
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
                      'NOTIFY YOUR CIRCLE',
                      textAlign: TextAlign.center,
                      style: TextStyle(letterSpacing: 1, color: Color(0xFFB35440), fontWeight: FontWeight.w700, fontSize: 12),
                    ),
                  ),
                  const SizedBox(width: 40),
                ],
              ),
              const SizedBox(height: 20),
              Text.rich(
                const TextSpan(
                  style: TextStyle(color: Color(0xFFB0503C), fontSize: 26, fontFamily: 'serif', height: 1.3),
                  children: [
                    TextSpan(text: "Let someone\n"),
                    TextSpan(text: 'know.', style: TextStyle(fontStyle: FontStyle.italic)),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                "They'll get a gentle message that you could use a check-in — nothing more.",
                style: TextStyle(color: Color(0xFFC17A63), fontSize: 14, height: 1.4),
              ),
              const SizedBox(height: 24),
              ...provider.circleContacts.map(
                (contact) => CircleContactTile(
                  contact: contact,
                  selected: _selected.contains(contact.name),
                  onTap: () {
                    if (contact.notified) return;
                    setState(() {
                      _selected.contains(contact.name) ? _selected.remove(contact.name) : _selected.add(contact.name);
                    });
                  },
                ),
              ),
              const SizedBox(height: 20),
              if (_sent)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                  child: const Row(
                    children: [
                      Icon(Icons.check_circle, color: AppColors.progressActive),
                      SizedBox(width: 12),
                      Expanded(child: Text('Sent. They should see it shortly.', style: TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600))),
                    ],
                  ),
                )
              else
                PrimaryButton(
                  label: _selected.isEmpty ? 'Select at least one person' : 'Notify ${_selected.length} ${_selected.length == 1 ? 'person' : 'people'}',
                  icon: null,
                  loading: _sending,
                  onPressed: _selected.isEmpty
                      ? null
                      : () async {
                          setState(() => _sending = true);
                          await context.read<AccountProvider>().notifyCircle(_selected.toList());
                          if (!mounted) return;
                          setState(() {
                            _sending = false;
                            _sent = true;
                          });
                        },
                ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}