// @see https://gist.github.com/codeincontext/1285806/c47a3b1cdcab3e0bf2b22ddd4a7720e63e166c89
export default function timeAgo(time) {
  let units = [
    { name: "second", limit: 60, in_seconds: 1 },
    { name: "minute", limit: 3600, in_seconds: 60 },
    { name: "hour", limit: 86400, in_seconds: 3600 },
    { name: "day", limit: 604800, in_seconds: 86400 },
    { name: "week", limit: 2629743, in_seconds: 604800 },
    { name: "month", limit: 31556926, in_seconds: 2629743 },
    { name: "year", limit: null, in_seconds: 31556926 },
  ];
  let diff = (new Date() - time) / 1000;
  if (diff < 5) return "now";

  let i = 0;
  let unit;
  while ((unit = units[i++])) {
    if (diff < unit.limit || !unit.limit) {
      diff = Math.floor(diff / unit.in_seconds);
      return diff + " " + unit.name + (diff > 1 ? "s" : "");
    }
  }
}
