import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/hospital_data.dart';

class HospitalTile extends StatelessWidget {
  const HospitalTile({super.key, required this.hospital, required this.onCall});
  final Hospital hospital;
  final VoidCallback onCall;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: const Color(0xFFF6D9CE), borderRadius: BorderRadius.circular(14)),
            child: const Icon(Icons.local_hospital_outlined, color: AppColors.sos, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(hospital.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textDark)),
                const SizedBox(height: 2),
                Text(hospital.address, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                const SizedBox(height: 4),
                Text(
                  '${hospital.distanceKm.toStringAsFixed(1)} km away${hospital.isOpen24h ? ' · Open 24h' : ''}',
                  style: const TextStyle(fontSize: 12, color: AppColors.progressActive, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
          Material(
            color: const Color(0xFFDCEAE2),
            shape: const CircleBorder(),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: onCall,
              child: const SizedBox(
                width: 42,
                height: 42,
                child: Icon(Icons.phone, color: AppColors.progressActive, size: 18),
              ),
            ),
          ),
        ],
      ),
    );
  }
}