import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';

import '../../core/services/api_client.dart';
import '../../core/theme/app_colors.dart';

/// Plays a dua or surah recitation. The backend's audio links expire after
/// about five minutes, so [fetchUrl] is called right before playing (and
/// again if a paused link has gone stale) instead of reusing an old one.
class RecitationPlayer extends StatefulWidget {
  const RecitationPlayer({super.key, required this.fetchUrl, this.player});

  /// Returns a fresh signed audio URL, or null if there is no recitation.
  final Future<String?> Function() fetchUrl;

  /// For tests.
  final AudioPlayer? player;

  @override
  State<RecitationPlayer> createState() => _RecitationPlayerState();
}

class _RecitationPlayerState extends State<RecitationPlayer> {
  late final AudioPlayer _player = widget.player ?? AudioPlayer();
  final List<StreamSubscription<dynamic>> _subs = [];

  PlayerState _state = PlayerState.stopped;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _loading = false;
  bool _hasSource = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _subs.addAll([
      _player.onPlayerStateChanged.listen((s) => setState(() => _state = s)),
      _player.onPositionChanged.listen((p) => setState(() => _position = p)),
      _player.onDurationChanged.listen((d) => setState(() => _duration = d)),
      _player.onPlayerComplete.listen((_) => setState(() {
            _position = Duration.zero;
            _hasSource = false; // fetch a fresh link next time
          })),
    ]);
  }

  @override
  void dispose() {
    for (final s in _subs) {
      s.cancel();
    }
    _player.dispose();
    super.dispose();
  }

  Future<void> _playFresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final url = await widget.fetchUrl();
      if (!mounted) return;
      if (url == null) {
        setState(() => _error = 'No recitation for this yet.');
        return;
      }
      await _player.play(UrlSource(url), position: _position);
      _hasSource = true;
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = "Couldn't play the recitation. Please try again.");
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggle() async {
    if (_loading) return;
    if (_state == PlayerState.playing) {
      await _player.pause();
      return;
    }
    if (_hasSource) {
      try {
        await _player.resume();
        return;
      } catch (_) {
        // The link has probably expired; get a new one below.
      }
    }
    await _playFresh();
  }

  String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return d.inHours > 0 ? '${d.inHours}:$m:$s' : '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    final playing = _state == PlayerState.playing;
    final max = _duration.inMilliseconds.toDouble();
    final value = max <= 0 ? 0.0 : _position.inMilliseconds.clamp(0, _duration.inMilliseconds).toDouble();

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 18, 12),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.10), borderRadius: BorderRadius.circular(20)),
      child: Column(
        children: [
          Row(
            children: [
              Semantics(
                button: true,
                label: playing ? 'Pause recitation' : 'Play recitation',
                child: GestureDetector(
                  onTap: _toggle,
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: _loading
                        ? const Padding(
                            padding: EdgeInsets.all(14),
                            child: CircularProgressIndicator(strokeWidth: 2.4, color: AppColors.audioCardEnd),
                          )
                        : Icon(playing ? Icons.pause : Icons.play_arrow, color: AppColors.audioCardEnd, size: 26),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    trackHeight: 3,
                    thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                    overlayShape: SliderComponentShape.noOverlay,
                    activeTrackColor: Colors.white,
                    inactiveTrackColor: Colors.white24,
                    thumbColor: Colors.white,
                  ),
                  child: Slider(
                    value: value,
                    max: max <= 0 ? 1 : max,
                    onChanged: max <= 0 ? null : (v) => _player.seek(Duration(milliseconds: v.round())),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                max <= 0 ? '--:--' : '${_fmt(_position)} / ${_fmt(_duration)}',
                style: const TextStyle(color: Colors.white70, fontSize: 11, fontFeatures: [FontFeature.tabularFigures()]),
              ),
            ],
          ),
          if (_error != null) ...[
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(_error!, style: const TextStyle(color: Color(0xFFF5C6B8), fontSize: 12)),
            ),
          ],
        ],
      ),
    );
  }
}
