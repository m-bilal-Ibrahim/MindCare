import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/therapy_provider.dart';
import '../../widgets/common/sos_button.dart';

class InSessionScreen extends StatefulWidget {
  const InSessionScreen({super.key});

  @override
  State<InSessionScreen> createState() => _InSessionScreenState();
}

class _InSessionScreenState extends State<InSessionScreen> {
  Timer? _timer;
  int _elapsedSeconds = 12 * 60 + 34;
  bool _micOn = true;
  bool _camOn = true;
  bool _captionsOn = false;

  final List<_InCallMessage> _chatMessages = [];
  final _chatController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsedSeconds++);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _chatController.dispose();
    super.dispose();
  }

  String get _formattedTime {
    final minutes = (_elapsedSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (_elapsedSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  void _openChat(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF241611),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        return Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
          child: StatefulBuilder(
            builder: (sheetContext, setSheetState) {
              return SafeArea(
                child: SizedBox(
                  height: 420,
                  child: Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
                        child: Row(
                          children: [
                            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
                          ],
                        ),
                      ),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 20),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text('In-call chat', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Expanded(
                        child: _chatMessages.isEmpty
                            ? const Center(
                                child: Text('No messages yet — say hi.', style: TextStyle(color: Colors.white38, fontSize: 13)),
                              )
                            : ListView.builder(
                                padding: const EdgeInsets.symmetric(horizontal: 20),
                                itemCount: _chatMessages.length,
                                itemBuilder: (context, index) {
                                  final msg = _chatMessages[index];
                                  return Align(
                                    alignment: msg.fromMe ? Alignment.centerRight : Alignment.centerLeft,
                                    child: Container(
                                      margin: const EdgeInsets.only(bottom: 10),
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                      decoration: BoxDecoration(
                                        color: msg.fromMe ? AppColors.progressActive : Colors.white12,
                                        borderRadius: BorderRadius.circular(16),
                                      ),
                                      child: Text(msg.text, style: const TextStyle(color: Colors.white, fontSize: 14)),
                                    ),
                                  );
                                },
                              ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                        child: Row(
                          children: [
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 16),
                                decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(24)),
                                child: TextField(
                                  controller: _chatController,
                                  style: const TextStyle(color: Colors.white),
                                  decoration: const InputDecoration(
                                    border: InputBorder.none,
                                    hintText: 'Message',
                                    hintStyle: TextStyle(color: Colors.white38),
                                    contentPadding: EdgeInsets.symmetric(vertical: 12),
                                  ),
                                  onSubmitted: (value) {
                                    if (value.trim().isEmpty) return;
                                    setSheetState(() => _chatMessages.add(_InCallMessage(value.trim(), true)));
                                    setState(() {});
                                    _chatController.clear();
                                  },
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            IconButton(
                              onPressed: () {
                                final value = _chatController.text.trim();
                                if (value.isEmpty) return;
                                setSheetState(() => _chatMessages.add(_InCallMessage(value, true)));
                                setState(() {});
                                _chatController.clear();
                              },
                              icon: const Icon(Icons.send, color: Colors.white),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  void _openMoreOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF241611),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SwitchListTile(
                      title: const Text('Captions', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                      subtitle: const Text('Show live captions during the call.', style: TextStyle(color: Colors.white54, fontSize: 12)),
                      value: _captionsOn,
                      activeThumbColor: AppColors.progressActive,
                      onChanged: (value) {
                        setSheetState(() => _captionsOn = value);
                        setState(() {});
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.report_gmailerrorred_outlined, color: Colors.white),
                      title: const Text('Report a technical issue', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Thanks — we\'ve logged this session for review.')),
                        );
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final therapist = context.watch<TherapyProvider>().selectedTherapist;
    final name = therapist?.name ?? 'Your therapist';

    return Scaffold(
      backgroundColor: const Color(0xFF241611),
      body: SafeArea(
        child: Container(
          decoration: const BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0, -0.2),
              radius: 1.2,
              colors: [Color(0xFF5A3A24), Color(0xFF241611)],
            ),
          ),
          child: Stack(
            children: [
              Positioned(
                top: 16,
                left: 16,
                right: 16,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(color: Colors.black.withOpacity(0.35), borderRadius: BorderRadius.circular(20)),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFFE5382B), shape: BoxShape.circle)),
                          const SizedBox(width: 6),
                          const Text('MEET · LIVE', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                          const SizedBox(width: 8),
                          Text(_formattedTime, style: const TextStyle(color: Colors.white70, fontSize: 11)),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(color: Colors.black.withOpacity(0.35), borderRadius: BorderRadius.circular(20)),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.auto_awesome, size: 13, color: Colors.white),
                          SizedBox(width: 6),
                          Text('Aida is taking notes', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                top: 76,
                right: 16,
                child: Container(
                  width: 108,
                  height: 148,
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFB4707A), Color(0xFF6E3A44)],
                    ),
                  ),
                  child: Stack(
                    children: [
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Icon(_micOn ? Icons.mic_none : Icons.mic_off, size: 14, color: Colors.white70),
                      ),
                      const Positioned(
                        left: 10,
                        bottom: 8,
                        child: Text('You', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                ),
              ),
              Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 130,
                      height: 130,
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.12), shape: BoxShape.circle),
                    ),
                    const SizedBox(height: 34),
                    Text(name, style: const TextStyle(color: Colors.white, fontSize: 26, fontFamily: 'serif')),
                    const SizedBox(height: 6),
                    const Text('Speaking...', style: TextStyle(color: Colors.white60, fontSize: 14)),
                  ],
                ),
              ),
              if (_captionsOn)
                Positioned(
                  left: 16,
                  right: 16,
                  bottom: 128,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                    decoration: BoxDecoration(color: Colors.black.withOpacity(0.4), borderRadius: BorderRadius.circular(16)),
                    child: const Text(
                      '"Let\'s stay with that thought a moment — what does it sound like in your head?"',
                      style: TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
                    ),
                  ),
                ),
              Positioned(
                left: 16,
                right: 16,
                bottom: 24,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _ControlButton(icon: _micOn ? Icons.mic_none : Icons.mic_off, onTap: () => setState(() => _micOn = !_micOn)),
                    _ControlButton(icon: _camOn ? Icons.videocam_outlined : Icons.videocam_off_outlined, onTap: () => setState(() => _camOn = !_camOn)),
                    _ControlButton(
                      icon: Icons.chat_bubble_outline,
                      badgeCount: _chatMessages.length,
                      onTap: () => _openChat(context),
                    ),
                    _ControlButton(icon: Icons.more_horiz, onTap: () => _openMoreOptions(context)),
                    _EndCallButton(onTap: () => Navigator.of(context).maybePop()),
                  ],
                ),
              ),
              const Positioned(right: 16, bottom: 100, child: SosButton()),
            ],
          ),
        ),
      ),
    );
  }
}

class _InCallMessage {
  _InCallMessage(this.text, this.fromMe);
  final String text;
  final bool fromMe;
}

class _ControlButton extends StatelessWidget {
  const _ControlButton({required this.icon, required this.onTap, this.badgeCount = 0});
  final IconData icon;
  final VoidCallback onTap;
  final int badgeCount;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), shape: BoxShape.circle),
            child: Icon(icon, color: Colors.white, size: 20),
          ),
          if (badgeCount > 0)
            Positioned(
              top: -2,
              right: -2,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: const BoxDecoration(color: AppColors.sos, shape: BoxShape.circle),
                constraints: const BoxConstraints(minWidth: 18, minHeight: 18),
                child: Text('$badgeCount', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w700)),
              ),
            ),
        ],
      ),
    );
  }
}

class _EndCallButton extends StatelessWidget {
  const _EndCallButton({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: const BoxDecoration(color: Color(0xFFD8664B), shape: BoxShape.circle),
        child: const Icon(Icons.call_end, color: Colors.white, size: 20),
      ),
    );
  }
}