export default class DateTimeHelpers {
  static getStartOfWeek(date) {
    let startOfWeek = new Date(date.getTime());
    startOfWeek.setDate(
      startOfWeek.getDate() -
        (startOfWeek.getDay() === 0 ? 6 : startOfWeek.getDay() - 1)
    );
    startOfWeek.setHours(0, 0, 0);
    startOfWeek.setMilliseconds(0);

    return startOfWeek;
  }

  static getEndOfWeek(date) {
    let endOfWeek = DateTimeHelpers.getStartOfWeek(date);
    endOfWeek.setDate(endOfWeek.getDate() + 6);
    endOfWeek.getHours(23, 59, 59);

    return endOfWeek;
  }

  static diffHours(date1, date2) {
    return Math.abs(date2.getTime() - date1.getTime()) / 1000 / 3600
  }

  static getShortMonth(date) {
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    return months[date.getMonth()];
  }
}
