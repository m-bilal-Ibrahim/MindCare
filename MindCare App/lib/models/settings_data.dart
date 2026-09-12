class NotificationCategory {
  const NotificationCategory({required this.id, required this.title, required this.subtitle, required this.enabled});
  final String id;
  final String title;
  final String subtitle;
  final bool enabled;

  NotificationCategory copyWith({bool? enabled}) {
    return NotificationCategory(id: id, title: title, subtitle: subtitle, enabled: enabled ?? this.enabled);
  }
}

class PrivacyToggle {
  const PrivacyToggle({required this.id, required this.title, required this.subtitle, required this.enabled, this.locked = false});
  final String id;
  final String title;
  final String subtitle;
  final bool enabled;
  final bool locked;

  PrivacyToggle copyWith({bool? enabled}) {
    return PrivacyToggle(id: id, title: title, subtitle: subtitle, enabled: enabled ?? this.enabled, locked: locked);
  }
}

class WearableDevice {
  const WearableDevice({
    required this.name,
    required this.model,
    required this.batteryPercent,
    required this.lastSynced,
    required this.connected,
  });

  final String name;
  final String model;
  final int batteryPercent;
  final String lastSynced;
  final bool connected;
}