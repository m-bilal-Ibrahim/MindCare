import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/community_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/onboarding/selectable_chip.dart';

class PeerTalkScreen extends StatefulWidget {
  const PeerTalkScreen({super.key});

  @override
  State<PeerTalkScreen> createState() => _PeerTalkScreenState();
}

class _PeerTalkScreenState extends State<PeerTalkScreen> {
  late final TextEditingController _noteController;

  @override
  void initState() {
    super.initState();
    final provider = context.read<CommunityProvider>();
    _noteController = TextEditingController(text: provider.noteText);
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CommunityProvider>();

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
                    'PEER TALK',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                IconButton(onPressed: () {}, icon: const Icon(Icons.more_horiz, color: AppColors.textDark)),
              ],
            ),
            const SizedBox(height: 6),
            Text.rich(
              TextSpan(
                style: AppTextStyles.heading(size: 30),
                children: [
                  const TextSpan(text: 'Someone can '),
                  TextSpan(text: 'listen.', style: AppTextStyles.heading(size: 30, style: FontStyle.italic)),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Post an anonymous note. The first listener who accepts gets matched to you for a 1-on-1 call · voices are softly masked.',
              style: AppTextStyles.body(size: 14),
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(20)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('HOW IT WORKS', style: TextStyle(letterSpacing: 1, color: AppColors.infoBoxText, fontWeight: FontWeight.w700, fontSize: 11)),
                  const SizedBox(height: 12),
                  _StepRow(number: 1, text: 'Write a note · stay anonymous'),
                  _StepRow(number: 2, text: 'One listener accepts · note vanishes'),
                  _StepRow(number: 3, text: 'You both join a private call (voice-masked)'),
                  _StepRow(number: 4, text: 'Either can leave or report any time', showDivider: false),
                ],
              ),
            ),
            const SizedBox(height: 22),
            Text('HOW ARE YOU RIGHT NOW?', style: AppTextStyles.label()),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(color: AppColors.progressTrack.withOpacity(0.4), borderRadius: BorderRadius.circular(18)),
              child: Row(
                children: CommunityProvider.feelingOptions.map((feeling) {
                  final selected = provider.selectedFeeling == feeling;
                  return Expanded(
                    child: GestureDetector(
                      onTap: () => context.read<CommunityProvider>().selectFeeling(feeling),
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 3),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(color: selected ? Colors.white : Colors.transparent, borderRadius: BorderRadius.circular(14)),
                        child: Text(
                          feeling,
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 13, fontWeight: selected ? FontWeight.w700 : FontWeight.w500, color: AppColors.textDark),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 20),
            Text("WHAT'S GOING ON (OPTIONAL)", style: AppTextStyles.label()),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: CommunityProvider.topicOptions.map((topic) {
                final selected = provider.selectedTopics.contains(topic);
                return SelectableChip(
                  label: topic,
                  selected: selected,
                  onTap: () => context.read<CommunityProvider>().toggleTopic(topic),
                );
              }).toList(),
            ),
            const SizedBox(height: 22),
            Text('A FEW LINES FOR YOUR LISTENER', style: AppTextStyles.label()),
            const SizedBox(height: 10),
            Container(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
              child: TextField(
                controller: _noteController,
                onChanged: (value) => context.read<CommunityProvider>().setNoteText(value),
                maxLines: 3,
                maxLength: 300,
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                  counterText: '',
                ),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 58,
                    child: ElevatedButton.icon(
                      onPressed: provider.postingRequest ? null : () => context.read<CommunityProvider>().postPeerTalkRequest(),
                      icon: provider.postingRequest
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.graphic_eq, color: Colors.white, size: 18),
                      label: Text(provider.postingRequest ? 'Posting...' : 'Post · find a listener', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF33415E),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                const SosButton(),
              ],
            ),
            const SizedBox(height: 10),
            Text('Usually matched within 4 minutes.', textAlign: TextAlign.center, style: AppTextStyles.body(size: 12)),
          ],
        ),
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({required this.number, required this.text, this.showDivider = true});
  final int number;
  final String text;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Row(
            children: [
              Container(
                width: 26,
                height: 26,
                decoration: const BoxDecoration(color: AppColors.infoBoxText, shape: BoxShape.circle),
                child: Center(child: Text('$number', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12))),
              ),
              const SizedBox(width: 14),
              Expanded(child: Text(text, style: const TextStyle(color: AppColors.infoBoxText, fontSize: 14))),
            ],
          ),
        ),
        if (showDivider) Divider(height: 1, color: AppColors.infoBoxText.withOpacity(0.15)),
      ],
    );
  }
}