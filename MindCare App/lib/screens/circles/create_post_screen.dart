import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/community_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/common/sos_button.dart';

class CreatePostScreen extends StatefulWidget {
  const CreatePostScreen({super.key, this.initialCircle});
  final String? initialCircle;

  @override
  State<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends State<CreatePostScreen> {
  final _controller = TextEditingController();
  late String _selectedCircle;
  bool _posting = false;

  @override
  void initState() {
    super.initState();
    final provider = context.read<CommunityProvider>();
    _selectedCircle = widget.initialCircle ?? provider.circleTags.first.name;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_controller.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Write something before posting.')),
      );
      return;
    }

    setState(() => _posting = true);
    await Future.delayed(const Duration(milliseconds: 500));
    context.read<CommunityProvider>().createPost(circleName: _selectedCircle, content: _controller.text);

    if (!mounted) return;
    setState(() => _posting = false);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CommunityProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: ListView(
            children: [
              const SizedBox(height: 8),
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.close, color: AppColors.textDark),
                  ),
                  const Expanded(
                    child: Text(
                      'NEW POST',
                      textAlign: TextAlign.center,
                      style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
              const SizedBox(height: 8),
              Text.rich(
                TextSpan(
                  style: AppTextStyles.heading(size: 28),
                  children: [
                    const TextSpan(text: 'Share with '),
                    TextSpan(text: 'your circle.', style: AppTextStyles.heading(size: 28, style: FontStyle.italic)),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text('Posts here are always anonymous — nobody sees your name.', style: AppTextStyles.body()),
              const SizedBox(height: 22),
              Text('POST TO', style: AppTextStyles.label()),
              const SizedBox(height: 10),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: provider.circleTags.map((tag) {
                  final selected = tag.name == _selectedCircle;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedCircle = tag.name),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: selected ? AppColors.chipSelected : AppColors.chipUnselected,
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: Text(
                        tag.name,
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: selected ? Colors.white : AppColors.chipTextUnselected),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 22),
              Text('YOUR POST', style: AppTextStyles.label()),
              const SizedBox(height: 10),
              Container(
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
                child: TextField(
                  controller: _controller,
                  maxLines: 6,
                  maxLength: 500,
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.all(16),
                    hintText: "What's on your mind? You're anonymous here.",
                    counterText: '',
                  ),
                ),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
                child: Row(
                  children: [
                    const Icon(Icons.shield_outlined, size: 16, color: AppColors.infoBoxText),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Posts are reviewed for safety before appearing. Avoid sharing personal details.',
                        style: TextStyle(fontSize: 12, color: AppColors.infoBoxText),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(child: PrimaryButton(label: 'Post anonymously', icon: null, loading: _posting, onPressed: _submit)),
                  const SizedBox(width: 12),
                  const SosButton(),
                ],
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}