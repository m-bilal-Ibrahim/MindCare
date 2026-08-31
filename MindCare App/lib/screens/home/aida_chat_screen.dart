import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/voice_input_service.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../models/checkin_data.dart';
import '../../providers/checkin_provider.dart';
import '../../widgets/chat/breathing_prompt_card.dart';
import '../../widgets/chat/chat_bubble.dart';
import '../../widgets/chat/quick_reply_row.dart';
import '../../providers/user_session_provider.dart';
import '../../main.dart';
import '../../models/breathing_data.dart';
import '../care/breathing_player_screen.dart';

class AidaChatScreen extends StatefulWidget {
  const AidaChatScreen({super.key});

  @override
  State<AidaChatScreen> createState() => _AidaChatScreenState();
}

class _AidaChatScreenState extends State<AidaChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  bool _isListening = false;
  bool _micUnavailable = false;
  String _textBeforeListening = '';

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    if (_isListening) VoiceInputService.instance.cancelListening();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send([String? preset]) {
    final text = preset ?? _controller.text;
    if (text.trim().isEmpty) return;
    if (_isListening) _stopListening(clearIfEmpty: false);
    context.read<CheckinProvider>().sendMessage(text);
    _controller.clear();
    _scrollToBottom();
  }

    Future<void> _toggleListening() async {
    if (_micUnavailable) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Microphone isn't available — check your browser/site permissions.")),
      );
      return;
    }

    if (_isListening) {
      _stopListening(clearIfEmpty: false);
      return;
    }

    _textBeforeListening = _controller.text;
    final started = await VoiceInputService.instance.startListening(
      onResult: (text, isFinal) {
        if (!mounted) return;
        final combined = _textBeforeListening.isEmpty ? text : '$_textBeforeListening $text';
        setState(() {
          _controller.text = combined;
          _controller.selection = TextSelection.collapsed(offset: _controller.text.length);
        });
        if (isFinal) {
          setState(() => _isListening = false);
        }
      },
    );

    if (!mounted) return;

    if (!started) {
      setState(() => _micUnavailable = true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Microphone isn't available — check your browser/site permissions.")),
      );
      return;
    }

    setState(() => _isListening = true);
  }
  void _stopListening({required bool clearIfEmpty}) {
    VoiceInputService.instance.stopListening();
    if (!mounted) return;
    setState(() => _isListening = false);
    if (clearIfEmpty && _controller.text.trim().isEmpty) {
      _controller.clear();
    }
  }

   @override
  Widget build(BuildContext context) {
    final provider = context.watch<CheckinProvider>();
    final firstName = context.watch<UserSessionProvider>().firstName;
    provider.personalizeGreeting(firstName);
    _scrollToBottom();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 8, 16, 8),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.chevron_left, color: AppColors.textDark),
                  ),
                  Container(
                    width: 40,
                    height: 40,
                    decoration: const BoxDecoration(color: Color(0xFF8C9EEB), shape: BoxShape.circle),
                    child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Aida', style: AppTextStyles.heading(size: 18)),
                        Row(
                          children: [
                            Container(width: 6, height: 6, decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle)),
                            const SizedBox(width: 4),
                            Text('always here', style: AppTextStyles.body(size: 11)),
                          ],
                        ),
                      ],
                    ),
                  ),
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    style: OutlinedButton.styleFrom(
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                      side: const BorderSide(color: AppColors.border),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    ),
                    child: const Text('End chat', style: TextStyle(color: AppColors.textDark, fontSize: 12)),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                controller: _scrollController,
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                children: [
                  Center(
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(20)),
                      child: Text('Today · 7:42 AM', style: AppTextStyles.body(size: 11)),
                    ),
                  ),
                  ...provider.messages.map((message) {
                    if (message.exercise != null) {
                      return BreathingPromptCard(
                        exercise: message.exercise!,
                        onBegin: () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const MobileFrame(child: BreathingPlayerScreen(pattern: BreathingPattern.quickBreath))),
                        ),
                      );
                    }
                    return ChatBubble(text: message.text ?? '', isUser: message.sender == MessageSender.user);
                  }),
                  if (provider.isAssistantTyping)
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Padding(
                        padding: EdgeInsets.only(bottom: 14),
                        child: Text('Aida is typing…', style: TextStyle(color: AppColors.textMuted, fontStyle: FontStyle.italic)),
                      ),
                    ),
                ],
              ),
            ),
            if (_isListening)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(width: 8, height: 8, decoration: const BoxDecoration(color: AppColors.sos, shape: BoxShape.circle)),
                    const SizedBox(width: 8),
                    Text('Listening… tap the mic to stop', style: AppTextStyles.body(size: 12)),
                  ],
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: QuickReplyRow(suggestions: CheckinProvider.quickReplies, onTap: _send),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(30),
                  border: _isListening ? Border.all(color: AppColors.sos, width: 1.4) : null,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        decoration: InputDecoration(
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          filled: false,
                          contentPadding: const EdgeInsets.symmetric(vertical: 16),
                          hintText: _isListening ? 'Listening…' : "Tell me what's on your mind...",
                        ),
                        onSubmitted: (_) => _send(),
                      ),
                    ),
                                       IconButton(
                      onPressed: _toggleListening,
                      icon: Icon(
                        _isListening ? Icons.mic : Icons.mic_none_outlined,
                        color: _isListening
                            ? AppColors.sos
                            : _micUnavailable
                                ? AppColors.border
                                : AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}