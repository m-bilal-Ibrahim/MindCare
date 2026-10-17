import 'dart:async';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/services/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/validators.dart';
import '../../models/profile_data.dart';
import '../../providers/profile_provider.dart';
import '../../widgets/common/primary_button.dart';
import '../../widgets/profile/profile_widgets.dart';

/// View and edit patients/me: photo, date of birth, gender, phone, country,
/// city and preferred language. The full name is set at sign-up.
class PersonalDetailsScreen extends StatefulWidget {
  const PersonalDetailsScreen({super.key});

  @override
  State<PersonalDetailsScreen> createState() => _PersonalDetailsScreenState();
}

class _PersonalDetailsScreenState extends State<PersonalDetailsScreen> {
  final _phone = TextEditingController();
  final _city = TextEditingController();

  bool _filled = false;
  DateTime? _dob;
  Gender? _gender;
  RefItem? _country;
  RefItem? _language;

  List<RefItem> _countries = const [];
  List<RefItem> _languages = const [];
  String? _listsError;

  Map<String, String> _serverErrors = const {};
  final Set<String> _touched = {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ProfileProvider>().ensureLoaded();
      _loadLists();
    });
  }

  Future<void> _loadLists() async {
    final p = context.read<ProfileProvider>();
    try {
      final results = await Future.wait([p.countries(), p.languages()]);
      if (!mounted) return;
      setState(() {
        _countries = results[0];
        _languages = results[1];
        _listsError = null;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _listsError = e.message);
    }
  }

  void _fillFrom(PatientProfile p) {
    if (_filled) return;
    _filled = true;
    _dob = p.dateOfBirth;
    _gender = p.gender;
    _country = p.country;
    _language = p.language;
    _phone.text = p.phoneNumber ?? '';
    _city.text = p.city?.name ?? '';
  }

  @override
  void dispose() {
    _phone.dispose();
    _city.dispose();
    super.dispose();
  }

  String? _phoneError() => _serverErrors['phone_number'] ?? (_touched.contains('phone') ? Validators.phoneNumber(_phone.text) : null);
  String? _cityError() => _serverErrors['city'] ?? (_touched.contains('city') ? Validators.personName(_city.text, label: 'City') : null);
  String? _dobError() => _serverErrors['date_of_birth'] ?? Validators.dateOfBirth(_dob);

  bool get _valid =>
      Validators.phoneNumber(_phone.text) == null && Validators.personName(_city.text, label: 'City') == null && Validators.dateOfBirth(_dob) == null;

  Map<String, dynamic> _changes(PatientProfile p) {
    String ymd(DateTime d) => '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    final changes = <String, dynamic>{};
    if (_dob != null && (p.dateOfBirth == null || ymd(_dob!) != ymd(p.dateOfBirth!))) changes['date_of_birth'] = ymd(_dob!);
    if (_gender != p.gender) changes['gender'] = _gender?.api;
    final phone = Validators.normalizeLine(_phone.text);
    if (phone != (p.phoneNumber ?? '') && Validators.normalizePhone(phone) != (p.phoneNumber ?? '')) changes['phone_number'] = phone;
    if (_country?.code != p.country?.code) changes['country'] = _country?.code;
    final city = Validators.normalizeLine(_city.text);
    if (city != (p.city?.name ?? '')) changes['city'] = city;
    if (_language?.code != p.language?.code) changes['preferred_language'] = _language?.code;
    return changes;
  }

  Future<void> _save(PatientProfile p) async {
    setState(() => _touched.addAll({'phone', 'city'}));
    if (!_valid) return;
    final changes = _changes(p);
    if (changes.isEmpty) return;
    final error = await context.read<ProfileProvider>().update(changes);
    if (!mounted) return;
    if (error == null) {
      setState(() => _serverErrors = const {});
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Your details are saved.')));
    } else {
      setState(() => _serverErrors = error.fieldErrors);
      if (error.fieldErrors.isEmpty || error.isSessionExpired) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dob ?? DateTime(now.year - 25, now.month, now.day),
      firstDate: DateTime(now.year - 120, now.month, now.day),
      lastDate: DateTime(now.year - 18, now.month, now.day),
      helpText: 'Date of birth',
    );
    if (picked != null) {
      setState(() {
        _dob = picked;
        _serverErrors = Map.of(_serverErrors)..remove('date_of_birth');
      });
    }
  }

  Future<void> _changePhoto(bool hasPhoto) async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (sheet) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined, color: AppColors.textDark),
              title: const Text('Choose from gallery'),
              onTap: () => Navigator.pop(sheet, 'gallery'),
            ),
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined, color: AppColors.textDark),
              title: const Text('Take a photo'),
              onTap: () => Navigator.pop(sheet, 'camera'),
            ),
            if (hasPhoto)
              ListTile(
                leading: const Icon(Icons.delete_outline, color: AppColors.sos),
                title: const Text('Remove photo', style: TextStyle(color: AppColors.sos)),
                onTap: () => Navigator.pop(sheet, 'remove'),
              ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
    if (choice == null || !mounted) return;
    final provider = context.read<ProfileProvider>();
    ApiException? error;
    if (choice == 'remove') {
      error = await provider.removePhoto();
    } else {
      XFile? file;
      try {
        file = await ImagePicker().pickImage(source: choice == 'camera' ? ImageSource.camera : ImageSource.gallery, maxWidth: 2048, imageQuality: 90);
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Couldn't open your photos. Check the app's permissions.")));
        }
        return;
      }
      if (file == null) return;
      final bytes = await file.readAsBytes();
      // Same limit as the backend, so the patient hears it straight away.
      if (bytes.length > 5 * 1024 * 1024) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Photo must be 5 MB or smaller.')));
        return;
      }
      error = await provider.uploadPhoto(bytes, file.name.isEmpty ? 'photo.jpg' : file.name);
    }
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error == null ? (choice == 'remove' ? 'Photo removed.' : 'Photo updated.') : (error.fieldErrors['photo'] ?? error.message))),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProfileProvider>();
    final state = provider.profile;
    final p = state.data;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          children: [
            const ProfileTopBar(label: 'PERSONAL DETAILS'),
            const SizedBox(height: 8),
            if (p == null && state.error != null)
              ProfileErrorCard(message: state.error!, sessionExpired: state.sessionExpired, onRetry: provider.load)
            else if (p == null)
              const ProfileFormSkeleton()
            else
              ..._form(context, provider, p),
          ],
        ),
      ),
    );
  }

  List<Widget> _form(BuildContext context, ProfileProvider provider, PatientProfile p) {
    _fillFrom(p);
    final changed = _changes(p).isNotEmpty;

    return [
      Center(
        child: ProfilePhoto(
          name: p.fullName,
          photoUrl: p.photoUrl,
          size: 96,
          busy: provider.saving,
          onTap: () => _changePhoto(p.photoUrl != null),
        ),
      ),
      const SizedBox(height: 10),
      Center(child: Text(p.fullName, style: AppTextStyles.heading(size: 22))),
      const SizedBox(height: 2),
      Center(child: Text('Shown to others as ${p.isPublic ? p.fullName : p.pseudonym}', style: AppTextStyles.body(size: 12))),
      const SizedBox(height: 24),
      const FieldLabel('DATE OF BIRTH'),
      PickerField(
        text: _dob == null ? 'Add your date of birth' : _formatDate(_dob!),
        placeholder: _dob == null,
        icon: Icons.cake_outlined,
        error: _dobError(),
        onTap: _pickDob,
      ),
      const FieldHint('Needed before you send a request to a psychologist. It can be corrected, but not removed once set.'),
      const SizedBox(height: 18),
      const FieldLabel('GENDER'),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          for (final g in Gender.values)
            ChoicePill(
              label: g.label,
              selected: _gender == g,
              onTap: () => setState(() {
                _gender = _gender == g ? null : g;
                _serverErrors = Map.of(_serverErrors)..remove('gender');
              }),
            ),
        ],
      ),
      if (_serverErrors['gender'] != null) FieldError(_serverErrors['gender']!),
      const SizedBox(height: 18),
      const FieldLabel('PHONE NUMBER'),
      TextField(
        controller: _phone,
        keyboardType: TextInputType.phone,
        autofillHints: const [AutofillHints.telephoneNumber],
        onChanged: (_) => setState(() {
          _touched.add('phone');
          _serverErrors = Map.of(_serverErrors)..remove('phone_number');
        }),
        decoration: profileInputDecoration('03001234567 or +923001234567', error: _phoneError()),
      ),
      const SizedBox(height: 18),
      const FieldLabel('COUNTRY'),
      DropdownField<RefItem>(
        value: _country,
        items: _countries,
        labelOf: (c) => c.name,
        hint: _countries.isEmpty ? (_listsError ?? 'Loading countries…') : 'Choose your country',
        error: _serverErrors['country'],
        onChanged: (c) => setState(() {
          if (c?.code != _country?.code) _city.clear();
          _country = c;
          _serverErrors = Map.of(_serverErrors)..remove('country');
        }),
      ),
      const SizedBox(height: 18),
      const FieldLabel('CITY'),
      CitySearchField(
        controller: _city,
        countryCode: _country?.code,
        error: _cityError(),
        onChanged: () => setState(() {
          _touched.add('city');
          _serverErrors = Map.of(_serverErrors)..remove('city');
        }),
        search: (country, q) => provider.cities(country, q),
      ),
      const SizedBox(height: 18),
      const FieldLabel('PREFERRED LANGUAGE'),
      DropdownField<RefItem>(
        value: _language,
        items: _languages,
        labelOf: (l) => l.name,
        hint: _languages.isEmpty ? (_listsError ?? 'Loading languages…') : 'Choose a language',
        error: _serverErrors['preferred_language'],
        onChanged: (l) => setState(() {
          _language = l;
          _serverErrors = Map.of(_serverErrors)..remove('preferred_language');
        }),
      ),
      if (_listsError != null) ...[
        const SizedBox(height: 6),
        TextButton(onPressed: _loadLists, child: const Text('Reload lists')),
      ],
      const SizedBox(height: 28),
      PrimaryButton(
        label: changed ? 'Save changes' : 'Saved',
        icon: changed ? Icons.check : null,
        loading: provider.saving,
        onPressed: changed && _valid ? () => _save(p) : null,
      ),
    ];
  }

  static String _formatDate(DateTime d) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    return '${d.day} ${months[d.month - 1]} ${d.year}';
  }
}

/// Text field with live suggestions from GET /reference/cities/. A city that
/// isn't listed can still be typed; the backend adds it as unverified.
class CitySearchField extends StatefulWidget {
  const CitySearchField({super.key, required this.controller, required this.countryCode, required this.search, required this.onChanged, this.error});

  final TextEditingController controller;
  final String? countryCode;
  final Future<List<City>> Function(String country, String query) search;
  final VoidCallback onChanged;
  final String? error;

  @override
  State<CitySearchField> createState() => _CitySearchFieldState();
}

class _CitySearchFieldState extends State<CitySearchField> {
  Timer? _debounce;
  List<City> _suggestions = const [];
  final _focus = FocusNode();

  @override
  void initState() {
    super.initState();
    _focus.addListener(() {
      if (!_focus.hasFocus) setState(() => _suggestions = const []);
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _focus.dispose();
    super.dispose();
  }

  void _onType(String text) {
    widget.onChanged();
    _debounce?.cancel();
    final country = widget.countryCode;
    final q = Validators.normalizeLine(text);
    if (country == null || q.length < 2) {
      setState(() => _suggestions = const []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      try {
        final found = await widget.search(country, q);
        if (mounted && _focus.hasFocus) setState(() => _suggestions = found);
      } on ApiException {
        if (mounted) setState(() => _suggestions = const []);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: widget.controller,
          focusNode: _focus,
          enabled: widget.countryCode != null,
          textCapitalization: TextCapitalization.words,
          onChanged: _onType,
          decoration: profileInputDecoration(widget.countryCode == null ? 'Choose a country first' : 'Start typing your city', error: widget.error),
        ),
        if (_suggestions.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 6),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppColors.border)),
            child: Column(
              children: [
                for (final c in _suggestions.take(6))
                  InkWell(
                    onTap: () {
                      widget.controller.text = c.name;
                      widget.onChanged();
                      setState(() => _suggestions = const []);
                      _focus.unfocus();
                    },
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      child: Row(
                        children: [
                          const Icon(Icons.place_outlined, size: 16, color: AppColors.textMuted),
                          const SizedBox(width: 10),
                          Expanded(child: Text(c.name, style: const TextStyle(color: AppColors.textDark))),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}
