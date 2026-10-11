import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../providers/community_provider.dart';
import '../../widgets/sos/hospital_tile.dart';

class NearbyHospitalsScreen extends StatelessWidget {
  const NearbyHospitalsScreen({super.key});

  /// Opens the phone's own dialer, pre-filled with the hospital's
  /// number — MindCare never places the call itself, same approach
  /// as the SOS helpline.
  Future<void> _callHospital(BuildContext context, String number) async {
    final uri = Uri(scheme: 'tel', path: number);
    final launched = await launchUrl(uri);
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Couldn't open the dialer. Call $number directly.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final hospitals = context.watch<CommunityProvider>().nearbyHospitals;

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
                    'NEARBY HOSPITALS',
                    textAlign: TextAlign.center,
                    style: TextStyle(letterSpacing: 1, color: AppColors.textLabel, fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
            const SizedBox(height: 8),
            Text('Help, close by.', style: AppTextStyles.heading(size: 26)),
            const SizedBox(height: 6),
            Text(
              hospitals.isEmpty
                  ? "We don't have hospitals for your area yet."
                  : '${hospitals.length} ${hospitals.length == 1 ? 'hospital' : 'hospitals'} near you, closest first.',
              style: AppTextStyles.body(),
            ),
            const SizedBox(height: 20),
            if (hospitals.isEmpty)
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('In an emergency', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textDark)),
                    const SizedBox(height: 4),
                    Text('Call Rescue 1122 for an ambulance, any time.', style: AppTextStyles.body(size: 13)),
                    const SizedBox(height: 14),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () => _callHospital(context, '1122'),
                        icon: const Icon(Icons.call, color: Colors.white, size: 18),
                        label: const Text('Call 1122', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.sos,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ...hospitals.map((hospital) {
              return HospitalTile(
                hospital: hospital,
                onCall: () => _callHospital(context, hospital.phoneNumber),
              );
            }),
          ],
        ),
      ),
    );
  }
}