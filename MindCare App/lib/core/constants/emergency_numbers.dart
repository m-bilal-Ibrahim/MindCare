import 'package:flutter/material.dart';

/// A national emergency or crisis number shown on the SOS screen.
class EmergencyNumber {
  const EmergencyNumber({
    required this.name,
    required this.display,
    required this.dial,
    required this.description,
    required this.icon,
    required this.color,
  });

  final String name;

  /// How the number is shown, e.g. "0311-7786264".
  final String display;

  /// What the phone dials, e.g. "03117786264".
  final String dial;
  final String description;
  final IconData icon;
  final Color color;
}

/// Fixed list of verified national numbers (Pakistan), until the SOS
/// backend serves admin-managed helplines and approved NGOs by city.
/// Only add a number here once it has been verified.
const List<EmergencyNumber> emergencyNumbers = [
  EmergencyNumber(
    name: 'Umang mental health helpline',
    display: '0311-7786264',
    dial: '03117786264',
    description: 'Trained listeners, in Urdu or English. Free.',
    icon: Icons.favorite_border,
    color: Color(0xFFD8664B),
  ),
  EmergencyNumber(
    name: 'Rescue 1122',
    display: '1122',
    dial: '1122',
    description: 'Ambulance and emergency rescue.',
    icon: Icons.local_hospital_outlined,
    color: Color(0xFFB0503C),
  ),
  EmergencyNumber(
    name: 'Police',
    display: '15',
    dial: '15',
    description: 'If you or someone else is in danger.',
    icon: Icons.local_police_outlined,
    color: Color(0xFF33415E),
  ),
  EmergencyNumber(
    name: 'Edhi ambulance',
    display: '115',
    dial: '115',
    description: 'Ambulance service across Pakistan.',
    icon: Icons.emergency_outlined,
    color: Color(0xFF4A7A67),
  ),
];
