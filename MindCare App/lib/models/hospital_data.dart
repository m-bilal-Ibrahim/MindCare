class Hospital {
  const Hospital({
    required this.name,
    required this.address,
    required this.distanceKm,
    required this.isOpen24h,
    required this.phoneNumber,
  });

  final String name;
  final String address;
  final double distanceKm;
  final bool isOpen24h;
  final String phoneNumber;
}