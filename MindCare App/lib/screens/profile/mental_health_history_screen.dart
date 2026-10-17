import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../models/profile_data.dart';
import '../../providers/profile_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/profile/profile_widgets.dart';

/// Optional mental health history (patients/me/history/). Saving replaces
/// the whole history, like the backend's PUT.
class MentalHealthHistoryScreen extends StatefulWidget {
  const MentalHealthHistoryScreen({super.key});

  @override
  State<MentalHealthHistoryScreen> createState() => _MentalHealthHistoryScreenState();
}

class _MentalHealthHistoryScreenState extends State<MentalHealthHistoryScreen> {
  final _notes = TextEditingController();
  List<RefItem>? _options;
  String? _optionsError;

  bool _filled = false;
  Set<String> _concerns = {};
  HistoryAnswer? _diagnosis;
  HistoryAnswer? _medication;
  HistoryAnswer? _therapy;
  Map<String, String> _serverErrors = const {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ProfileProvider>().loadHistory();
      _loadOptions();
    });
  }

  Future<void> _loadOptions() async {
    try {
      final o = await context.read<ProfileProvider>().specializations();
      if (mounted) setState(() => _options = o);
    } on ApiException catch (e) {
      if (mounted) setState(() => _optionsError = e.message);
    }
  }

  @override
  void dispose() {
    _notes.dispose();
    super.dispose();
  }

  void _fill(MentalHealthHistory h) {
    if (_filled) return;
    _filled = true;
    _concerns = h.concerns.map((c) => c.code).toSet();
    _diagnosis = h.previousDiagnosis;
    _medication = h.currentMedication;
    _therapy = h.previousTherapy;
    _notes.text = h.notes;
  }

  String? get _notesError => _serverErrors['notes'] ?? Validators.freeText(_notes.text, label: 'Notes', min: 10, max: 1000);

  Future<void> _save() async {
    if (_notesError != null) return;
    final h = MentalHealthHistory(
      concerns: [for (final code in _concerns) RefItem(code: code, name: code)],
      previousDiagnosis: _diagnosis,
      currentMedication: _medication,
      previousTherapy: _therapy,
      notes: Validators.normalizeMultiline(_notes.text),
    );
    final error = await context.read<ProfileProvider>().saveHistory(h);
    if (!mounted) return;
    if (error == null) {
      setState(() => _serverErrors = const {});
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Your history is saved.')));
    } else {
      setState(() => _serverErrors = error.fieldErrors);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    }
  }

  Future<void> _delete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (d) => AlertDialog(
        backgroundColor: AppColors.background,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Delete your history?', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
        content: Text('Everything on this page is removed from MindCare. You can add it again later.', style: AppTextStyles.body(size: 14)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(d, false), child: const Text('Keep it', style: TextStyle(color: AppColors.textMuted))),
          TextButton(onPressed: () => Navigator.pop(d, true), child: const Text('Delete', style: TextStyle(color: AppColors.sos, fontWeight: FontWeight.w700))),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    final error = await context.read<ProfileProvider>().deleteHistory();
    if (!mounted) return;
    if (error == null) {
      setState(() {
        _concerns = {};
        _diagnosis = _medication = _therapy = null;
        _notes.clear();
      });
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error?.message ?? 'Your history was deleted.')));
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProfileProvider>();
    final state = provider.history;
    final h = state.data;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          children: [
            const ProfileTopBar(label: 'MENTAL HEALTH HISTORY'),
            const SizedBox(height: 8),
            Text('Your history, if you want to share it.', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: AppColors.infoBoxBackground, borderRadius: BorderRadius.circular(16)),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.lock_outline, size: 18, color: AppColors.infoBoxText),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Optional. It is encrypted, and only you and your current psychologist can read it. Every time your psychologist opens it, that is recorded.',
                      style: TextStyle(fontSize: 12, color: AppColors.infoBoxText, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            if (h == null && state.error != null)
              ProfileErrorCard(message: state.error!, sessionExpired: state.sessionExpired, onRetry: provider.loadHistory)
            else if (h == null || _options == null && _optionsError == null)
              const ProfileFormSkeleton(fields: 4, withPhoto: false)
            else
              ..._form(provider, h),
          ],
        ),
      ),
    );
  }

  List<Widget> _form(ProfileProvider provider, MentalHealthHistory h) {
    _fill(h);
    final notesLength = Validators.normalizeMultiline(_notes.text).length;

    Widget question(String label, HistoryAnswer? value, List<HistoryAnswer> options, ValueChanged<HistoryAnswer?> onChanged) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FieldLabel(label),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final o in options) ChoicePill(label: o.label, selected: value == o, onTap: () => onChanged(value == o ? null : o)),
            ],
          ),
          const SizedBox(height: 18),
        ],
      );
    }

    return [
      const FieldLabel('WHAT ARE YOU DEALING WITH?'),
      if (_optionsError != null)
        Text(_optionsError!, style: AppTextStyles.body(size: 13))
      else
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final o in _options!)
              ChoicePill(
                label: o.name,
                selected: _concerns.contains(o.code),
                onTap: () => setState(() => _concerns.contains(o.code) ? _concerns.remove(o.code) : _concerns.add(o.code)),
              ),
          ],
        ),
      const SizedBox(height: 22),
      question('HAVE YOU BEEN DIAGNOSED BEFORE?', _diagnosis, HistoryAnswer.values, (v) => setState(() => _diagnosis = v)),
      question('ARE YOU TAKING MEDICATION FOR IT?', _medication, HistoryAnswer.values, (v) => setState(() => _medication = v)),
      question('HAVE YOU HAD THERAPY BEFORE?', _therapy, const [HistoryAnswer.yes, HistoryAnswer.no], (v) => setState(() => _therapy = v)),
      const FieldLabel('ANYTHING ELSE? (OPTIONAL)'),
      TextField(
        controller: _notes,
        minLines: 4,
        maxLines: 8,
        maxLength: 1000,
        textCapitalization: TextCapitalization.sentences,
        onChanged: (_) => setState(() => _serverErrors = Map.of(_serverErrors)..remove('notes')),
        decoration: profileInputDecoration('A few words your psychologist should know', error: _notes.text.trim().isEmpty ? null : _notesError).copyWith(
          counterText: '$notesLength / 1000',
        ),
      ),
      const SizedBox(height: 24),
      PrimaryButton(label: 'Save history', icon: Icons.check, loading: provider.saving, onPressed: _notesError == null ? _save : null),
      if (!h.isEmpty) ...[
        const SizedBox(height: 12),
        Center(
          child: TextButton(
            onPressed: provider.saving ? null : _delete,
            child: const Text('Delete my history', style: TextStyle(color: AppColors.sos, fontWeight: FontWeight.w600)),
          ),
        ),
      ],
    ];
  }
}
