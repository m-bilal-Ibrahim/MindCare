import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../widgets/common/primary_button.dart';

class MessageTherapistScreen extends StatefulWidget {
  const MessageTherapistScreen({super.key, required this.therapistName});
  final String therapistName;

  @override
  State<MessageTherapistScreen> createState() => _MessageTherapistScreenState();
}

class _MessageTherapistScreenState extends State<MessageTherapistScreen> {
  final _controller = TextEditingController();
  bool _sending = false;
  bool _sent = false;
  bool _hasText = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_sent) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 84,
                  height: 84,
                  decoration: const BoxDecoration(color: AppColors.progressActive, shape: BoxShape.circle),
                  child: const Icon(Icons.check, color: Colors.white, size: 36),
                ),
                const SizedBox(height: 24),
                Text('Sent.', style: AppTextStyles.heading(size: 26)),
                const SizedBox(height: 8),
                Text(
                  '${widget.therapistName} usually replies within 48 hours on weekdays.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.body(),
                ),
                const SizedBox(height: 32),
                PrimaryButton(label: 'Done', icon: null, onPressed: () => Navigator.of(context).pop()),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.close, color: AppColors.textDark),
                  ),
                  Expanded(
                    child: Text(
                      'MESSAGE ${widget.therapistName.toUpperCase()}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 11),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: ListView(
                  children: [
                    const SizedBox(height: 8),
                    Text('A quick note.', style: AppTextStyles.heading(size: 24)),
                    const SizedBox(height: 8),
                    Text('Not urgent? Great for questions between sessions.', style: AppTextStyles.body()),
                    const SizedBox(height: 20),
                    Container(
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                      child: TextField(
                        controller: _controller,
                        maxLines: 6,
                        onChanged: (value) => setState(() => _hasText = value.trim().isNotEmpty),
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.all(16),
                          hintText: "What's on your mind?",
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline, size: 16, color: AppColors.infoBoxText),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'For anything urgent, use the SOS button instead — messages aren\'t monitored in real time.',
                              style: TextStyle(fontSize: 12, color: AppColors.infoBoxText, height: 1.4),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
              child: PrimaryButton(
                label: 'Send message',
                icon: null,
                loading: _sending,
                onPressed: !_hasText
                    ? null
                    : () async {
                        setState(() => _sending = true);
                        await Future.delayed(const Duration(milliseconds: 500));
                        if (!mounted) return;
                        setState(() {
                          _sending = false;
                          _sent = true;
                        });
                      },
              ),
            ),
          ],
        ),
      ),
    );
  }
}