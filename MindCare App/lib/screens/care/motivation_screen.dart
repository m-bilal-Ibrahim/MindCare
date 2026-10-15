import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../main.dart';
import '../../models/motivation_data.dart';
import '../../providers/motivation_provider.dart';
import '../../widgets/common/sos_button.dart';
import '../../widgets/motivation/motivation_states.dart';
import '../../widgets/motivation/motivation_tab_bar.dart';
import 'dua_detail_screen.dart';
import 'surah_reader_screen.dart';

/// Motivation Corner (6.10), on the backend's data: a quote of the moment,
/// the quotes feed, and, only after the patient turns them on, duas and
/// surahs with recitations.
class MotivationScreen extends StatefulWidget {
  const MotivationScreen({super.key});

  @override
  State<MotivationScreen> createState() => _MotivationScreenState();
}

class _MotivationScreenState extends State<MotivationScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<MotivationProvider>().start();
    });
  }

  void _openSettings(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.motivationBgStart,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => const _ReligiousSettingsSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = context.watch<MotivationProvider>();

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [AppColors.motivationBgStart, AppColors.motivationBgEnd], begin: Alignment.topCenter, end: Alignment.bottomCenter),
        ),
        child: SafeArea(
          child: Stack(
            children: [
              ListView(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 110),
                children: [
                  Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.chevron_left, color: Colors.white),
                      ),
                      const Expanded(
                        child: Text(
                          'MOTIVATION',
                          textAlign: TextAlign.center,
                          style: TextStyle(letterSpacing: 1, color: Colors.white70, fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Motivation settings',
                        onPressed: () => _openSettings(context),
                        icon: const Icon(Icons.tune, color: Colors.white),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const _QuoteOfTheMoment(),
                  const SizedBox(height: 24),
                  MotivationTabBar(
                    tabs: MotivationProvider.tabs,
                    selected: p.selectedTab,
                    onChanged: (tab) => context.read<MotivationProvider>().selectTab(tab),
                  ),
                  const SizedBox(height: 20),
                  switch (p.selectedTab) {
                    'Duas' => const _ReligiousSection(kind: _ReligiousKind.duas),
                    'Surahs' => const _ReligiousSection(kind: _ReligiousKind.surahs),
                    _ => const _QuotesSection(),
                  },
                ],
              ),
              const Positioned(right: 0, bottom: 24, child: SosButton()),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuoteOfTheMoment extends StatelessWidget {
  const _QuoteOfTheMoment();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<MotivationProvider>().quoteOfMoment;
    final quote = state.data;

    Widget body;
    if (state.loading) {
      body = MotivationSkeleton(kind: MotivationSkeletonKind.quote, showWakeNote: quote == null);
    } else if (state.error != null && quote == null) {
      body = MotivationError(
        message: state.error!,
        sessionExpired: state.sessionExpired,
        onRetry: () => context.read<MotivationProvider>().loadQuoteOfMoment(),
      );
    } else if (quote == null) {
      body = const Text(
        'No quotes have been added yet.',
        textAlign: TextAlign.center,
        style: TextStyle(color: Colors.white70, fontSize: 18, fontFamily: 'serif'),
      );
    } else {
      body = Column(
        children: [
          Text(
            '“${quote.text}”',
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white, fontSize: 24, fontFamily: 'serif', height: 1.35),
          ),
          if (quote.author != null) ...[
            const SizedBox(height: 12),
            Text('— ${quote.author}', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white60, fontSize: 13, letterSpacing: 0.5)),
          ],
        ],
      );
    }

    return Column(
      children: [
        const Text('Today', textAlign: TextAlign.center, style: TextStyle(color: Colors.white60, fontFamily: 'serif', fontStyle: FontStyle.italic, fontSize: 18)),
        const SizedBox(height: 12),
        body,
        if (quote != null) ...[
          const SizedBox(height: 10),
          TextButton.icon(
            onPressed: state.loading ? null : () => context.read<MotivationProvider>().loadQuoteOfMoment(),
            icon: Icon(Icons.refresh, size: 16, color: state.loading ? Colors.white38 : Colors.white70),
            label: const Text('Another quote', style: TextStyle(color: Colors.white70)),
          ),
        ],
      ],
    );
  }
}

class _QuotesSection extends StatelessWidget {
  const _QuotesSection();

  @override
  Widget build(BuildContext context) {
    final p = context.watch<MotivationProvider>();

    Widget chip(String label, QuoteCategory? value) {
      final selected = p.category == value;
      // A plain pill rather than ChoiceChip: the app's chip theme paints
      // unselected chips cream, which made white labels unreadable here.
      return Padding(
        padding: const EdgeInsets.only(right: 8),
        child: Semantics(
          button: true,
          selected: selected,
          child: GestureDetector(
            onTap: () => context.read<MotivationProvider>().setCategory(value),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
              decoration: BoxDecoration(
                color: selected ? Colors.white : Colors.white.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                label,
                style: TextStyle(color: selected ? AppColors.motivationBgEnd : Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
              ),
            ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(children: [chip('All', null), for (final c in QuoteCategory.values) chip(c.label, c)]),
        ),
        const SizedBox(height: 16),
        if (p.quotes.isEmpty && p.quotesLoading)
          const MotivationSkeleton(kind: MotivationSkeletonKind.quoteCards, count: 4)
        else if (p.quotes.isEmpty && p.quotesError != null)
          MotivationError(
            message: p.quotesError!,
            sessionExpired: p.sessionExpired,
            onRetry: () => context.read<MotivationProvider>().loadQuotes(reset: true),
          )
        else if (p.quotes.isEmpty && p.quotesLoaded)
          MotivationMessage(
            icon: Icons.format_quote,
            title: 'No quotes here yet',
            body: p.category == null ? 'Quotes will appear here once they are added.' : 'Try another category.',
          )
        else ...[
          for (final q in p.quotes) _QuoteTile(quote: q),
          if (p.quotesError != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(p.quotesError!, style: const TextStyle(color: Color(0xFFF5C6B8), fontSize: 12)),
            ),
          if (p.quotesLoading)
            const MotivationSkeleton(kind: MotivationSkeletonKind.quoteCards, count: 2, showWakeNote: false)
          else if (p.quotesHasMore)
            Center(
              child: TextButton(
                onPressed: () => context.read<MotivationProvider>().loadQuotes(),
                child: const Text('Show more', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
              ),
            ),
        ],
      ],
    );
  }
}

class _QuoteTile extends StatelessWidget {
  const _QuoteTile({required this.quote});
  final Quote quote;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(18)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('“${quote.text}”', style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.45, fontFamily: 'serif')),
          if (quote.author != null || quote.category != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                if (quote.author != null)
                  Expanded(child: Text('— ${quote.author}', style: const TextStyle(color: Colors.white60, fontSize: 12)))
                else
                  const Spacer(),
                if (quote.category != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                    decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
                    child: Text(quote.category!.label, style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600)),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

enum _ReligiousKind { duas, surahs }

class _ReligiousSection extends StatefulWidget {
  const _ReligiousSection({required this.kind});
  final _ReligiousKind kind;

  @override
  State<_ReligiousSection> createState() => _ReligiousSectionState();
}

class _ReligiousSectionState extends State<_ReligiousSection> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final p = context.read<MotivationProvider>();
      if (p.optIn.data == null && !p.optIn.loading) p.loadOptIn();
    });
  }

  @override
  Widget build(BuildContext context) {
    final p = context.watch<MotivationProvider>();
    final optIn = p.optIn;

    if (optIn.loading || (optIn.data == null && optIn.error == null)) return const MotivationSkeleton(kind: MotivationSkeletonKind.rows);
    if (optIn.error != null) {
      return MotivationError(
        message: optIn.error!,
        sessionExpired: optIn.sessionExpired,
        onRetry: () => context.read<MotivationProvider>().loadOptIn(),
      );
    }
    if (optIn.data != true) return const _OptInCard();

    if (widget.kind == _ReligiousKind.duas) {
      final duas = p.duas;
      if (!duas.hasData && !duas.loading && duas.error == null) {
        WidgetsBinding.instance.addPostFrameCallback((_) => context.read<MotivationProvider>().loadDuas());
        return const MotivationSkeleton(kind: MotivationSkeletonKind.rows, count: 5);
      }
      if (duas.loading) return const MotivationSkeleton(kind: MotivationSkeletonKind.rows, count: 5);
      if (duas.error != null) {
        return MotivationError(message: duas.error!, sessionExpired: duas.sessionExpired, onRetry: () => context.read<MotivationProvider>().loadDuas());
      }
      if (duas.data!.isEmpty) {
        return const MotivationMessage(icon: Icons.menu_book_outlined, title: 'No duas yet', body: 'Duas will appear here once they are added.');
      }
      return Column(
        children: [
          for (final d in duas.data!)
            _ListRow(
              leading: const Icon(Icons.auto_stories_outlined, color: Colors.white, size: 18),
              title: d.title,
              subtitle: d.reference,
              trailingAudio: d.hasAudio,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => MobileFrame(child: DuaDetailScreen(dua: d))),
              ),
            ),
          const _Attribution(),
        ],
      );
    }

    final surahs = p.surahs;
    if (!surahs.hasData && !surahs.loading && surahs.error == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => context.read<MotivationProvider>().loadSurahs());
      return const MotivationSkeleton(kind: MotivationSkeletonKind.rows, count: 5);
    }
    if (surahs.loading) return const MotivationSkeleton(kind: MotivationSkeletonKind.rows, count: 5);
    if (surahs.error != null) {
      return MotivationError(message: surahs.error!, sessionExpired: surahs.sessionExpired, onRetry: () => context.read<MotivationProvider>().loadSurahs());
    }
    if (surahs.data!.isEmpty) {
      return const MotivationMessage(icon: Icons.menu_book_outlined, title: 'No surahs yet', body: 'Surahs will appear here once they are added.');
    }
    return Column(
      children: [
        for (final s in surahs.data!)
          _ListRow(
            leading: Text('${s.number}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
            title: s.nameEnglish,
            subtitle: '${s.nameMeaning} · ${s.ayahCount} ${s.ayahCount == 1 ? 'verse' : 'verses'}',
            trailingText: s.nameArabic,
            trailingAudio: s.hasAudio,
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => MobileFrame(child: SurahReaderScreen(summary: s))),
            ),
          ),
        const _Attribution(),
      ],
    );
  }
}

class _ListRow extends StatelessWidget {
  const _ListRow({required this.leading, required this.title, required this.subtitle, required this.onTap, this.trailingText, this.trailingAudio = false});
  final Widget leading;
  final String title;
  final String subtitle;
  final String? trailingText;
  final bool trailingAudio;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.white.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), shape: BoxShape.circle),
                  child: leading,
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                      const SizedBox(height: 2),
                      Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white60, fontSize: 12)),
                    ],
                  ),
                ),
                if (trailingText != null) ...[
                  const SizedBox(width: 8),
                  Text(trailingText!, textDirection: TextDirection.rtl, style: arabicStyle(size: 18)),
                ],
                if (trailingAudio) ...[
                  const SizedBox(width: 8),
                  const Icon(Icons.headphones_outlined, color: Colors.white54, size: 16),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _OptInCard extends StatelessWidget {
  const _OptInCard();

  @override
  Widget build(BuildContext context) {
    final p = context.watch<MotivationProvider>();
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(22)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.auto_stories_outlined, color: Colors.white, size: 26),
          const SizedBox(height: 12),
          const Text('Quran and duas', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          const Text(
            'Duas and short surahs with translation and recitation. This is optional and off unless you turn it on. You can turn it off any time in Motivation settings, which removes your choice from MindCare.',
            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.45),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: p.savingOptIn
                  ? null
                  : () async {
                      final error = await context.read<MotivationProvider>().setOptIn(true);
                      if (error != null && context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error)));
                      }
                    },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: AppColors.motivationBgEnd,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: p.savingOptIn
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2, color: AppColors.motivationBgEnd))
                  : const Text('Show Quran and duas', style: TextStyle(fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReligiousSettingsSheet extends StatelessWidget {
  const _ReligiousSettingsSheet();

  @override
  Widget build(BuildContext context) {
    final p = context.watch<MotivationProvider>();
    if (p.optIn.data == null && !p.optIn.loading && p.optIn.error == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => context.read<MotivationProvider>().loadOptIn());
    }
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(4)))),
            const SizedBox(height: 16),
            const Text('Motivation settings', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Show Quran and duas', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
              subtitle: const Text('Turning this off removes your choice from MindCare.', style: TextStyle(color: Colors.white60, fontSize: 12)),
              value: p.optIn.data == true,
              activeThumbColor: AppColors.motivationBgEnd,
              activeTrackColor: Colors.white,
              onChanged: (p.savingOptIn || p.optIn.data == null)
                  ? null
                  : (v) async {
                      final error = await context.read<MotivationProvider>().setOptIn(v);
                      if (error != null && context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error)));
                      }
                    },
            ),
            if (p.optIn.error != null) Text(p.optIn.error!, style: const TextStyle(color: Color(0xFFF5C6B8), fontSize: 12)),
            const SizedBox(height: 12),
            const Text(quranAttribution, style: TextStyle(color: Colors.white54, fontSize: 11, height: 1.4)),
          ],
        ),
      ),
    );
  }
}

class _Attribution extends StatelessWidget {
  const _Attribution();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(top: 8),
      child: Text(quranAttribution, style: TextStyle(color: Colors.white38, fontSize: 11, height: 1.4)),
    );
  }
}
