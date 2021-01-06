import render from "./render.js";
import dateTime from "./dateTime.js";

const MAX_WEEKS = 4;

export default class InVsOut {
  static init(cfg, events) {
    console.log("init in vs out...");

    const root = document.querySelector(".in-vs-out");

    render(root.querySelector(".content"), [cfg.pets]);

    let i = 0;
    for (const petEl of Array.from(root.querySelectorAll(".pet"))) {
      const pet = cfg.pets[i];
      const [weeks, inside, outside] = InVsOut.calculate(cfg, pet, events);

      const chartEl = petEl.querySelector(".chart");

      new chartXkcd.StackedBar(chartEl, {
        xLabel: "Period",
        yLabel: "Time (h)",
        data: {
          labels: weeks,
          datasets: [
            {
              label: "Inside",
              data: inside,
            },
            {
              label: "Outside",
              data: outside,
            },
          ],
        },
        options: {
          backgroundColor: "transparent",
          strokeColor: "var(--white)",
          dataColors: ["#94C5FA", "#6DFA97"].reverse(),
          legendPosition: chartXkcd.config.positionType.upRight,
        },
      });
      i++;
    }
  }

  static calculate(cfg, pet, events) {
    events = events.filter((i) => i.pets.includes(pet.id));
    events = events.filter(
      (i) =>
        i.event === cfg.events.WENT_OUTSIDE ||
        i.event === cfg.events.WENT_INSIDE
    );
    events = events.sort((a, b) => a.recordedAt - b.recordedAt);
    events.push({ event: "FIN", recordedAt: new Date() });

    let weekIndexMap = {};
    let weeks = [];
    let outside = [];
    let inside = [];

    const formatDate = (date) => {
      return date.getDate() + "/" + (date.getMonth() + 1);
    };

    const getWeekIndex = (date) => {
      const startOfWeek = dateTime.getStartOfWeek(date);
      const endOfWeek = dateTime.getEndOfWeek(date);
      const weekKey = startOfWeek.getTime();

      if (typeof weekIndexMap[weekKey] !== "undefined") {
        return weekIndexMap[weekKey];
      } else {
        weekIndexMap[weekKey] = weeks.length;
        weeks.push(formatDate(startOfWeek) + " - " + formatDate(endOfWeek));
        inside.push(0);
        outside.push(0);
      }
    };

    let state =
      events[0].event === cfg.events.WENT_OUTSIDE ? "inside" : "outside";
    let stateTime = events[0].recordedAt;

    for (const e of events) {
      if (
        state === "inside" &&
        (e.event === cfg.events.WENT_OUTSIDE || e.event === "FIN")
      ) {
        const weekIndex = getWeekIndex(e.recordedAt);
        inside[weekIndex] += dateTime.diffHours(stateTime, e.recordedAt);
        state = "outside";
        stateTime = e.recordedAt;
      } else if (
        state === "outside" &&
        (e.event === cfg.events.WENT_INSIDE || e.event === "FIN")
      ) {
        const weekIndex = getWeekIndex(e.recordedAt);
        outside[weekIndex] += dateTime.diffHours(stateTime, e.recordedAt);
        state = "inside";
        stateTime = e.recordedAt;
      }
    }

    inside = inside.map((i) => Math.round(i));
    outside = outside.map((i) => Math.round(i));

    if (weeks.length > MAX_WEEKS) {
      weeks = weeks.slice(weeks.length - MAX_WEEKS);
      inside = inside.slice(inside.length - MAX_WEEKS);
      outside = outside.slice(outside.length - MAX_WEEKS);
    }

    return [weeks, inside, outside];
  }
}
