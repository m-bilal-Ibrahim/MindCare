/// Small, dependency-free date and time labels used across the app.
class DateLabels {
  DateLabels._();

  static const _weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  static const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  /// "Fri"
  static String weekdayShort(DateTime t) => _weekdays[t.weekday - 1].substring(0, 3);

  /// "Oct"
  static String monthShort(DateTime t) => _months[t.month - 1];

  /// "2 hours ago", "just now", "3 days ago"
  static String ago(DateTime t) {
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return 'just now';
    if (d.inMinutes < 60) return '${d.inMinutes} min ago';
    if (d.inHours < 24) return '${d.inHours} ${d.inHours == 1 ? 'hour' : 'hours'} ago';
    return '${d.inDays} ${d.inDays == 1 ? 'day' : 'days'} ago';
  }

  static String time(DateTime t) {
    final hour = t.hour % 12 == 0 ? 12 : t.hour % 12;
    final minute = t.minute.toString().padLeft(2, '0');
    return '$hour:$minute ${t.hour < 12 ? 'AM' : 'PM'}';
  }

  static int _daysFromToday(DateTime t) {
    final now = DateTime.now();
    return DateTime(t.year, t.month, t.day).difference(DateTime(now.year, now.month, now.day)).inDays;
  }

  /// "Today", "Yesterday", "Tomorrow", a weekday within the week, else "12 Oct".
  static String day(DateTime t) {
    final d = _daysFromToday(t);
    if (d == 0) return 'Today';
    if (d == -1) return 'Yesterday';
    if (d == 1) return 'Tomorrow';
    if (d.abs() < 7) return _weekdays[t.weekday - 1];
    return '${t.day} ${_months[t.month - 1]}';
  }

  /// "Saturday, 11 Oct"
  static String long(DateTime t) => '${_weekdays[t.weekday - 1]}, ${t.day} ${_months[t.month - 1]}';

  static String duration(int minutes) {
    if (minutes < 60) return '$minutes min';
    final h = minutes ~/ 60;
    final m = minutes % 60;
    return m == 0 ? '$h hr' : '$h hr $m min';
  }
}
