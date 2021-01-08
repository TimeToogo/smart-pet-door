import render from "./render.js";
import timeago from "./timeago.js";

export default class Frequencies {
  static init(cfg, events) {
    console.log("init frequencies...");

    const LABELS = {};
    LABELS[cfg.events.SIGHTING] = {
      label: "In the courtyard",
      colour: "#75F4FA",
    };
    LABELS[cfg.events.WENT_INSIDE] = {
      label: "Went inside",
      colour: "#7EFA95",
    };
    LABELS[cfg.events.WENT_OUTSIDE] = {
      label: "Went outside",
      colour: "#FAE66E",
    };
    LABELS[cfg.events.HUNT] = { label: "On the hunt", colour: "#FAB243" };
    LABELS[cfg.events.FIGHT] = { label: "Having a brawl", colour: "#FA5563" };
    LABELS[cfg.events.TOILET] = { label: "Off to the loo", colour: "#AD6D53" };

    const root = document.querySelector(".frequencies");

    const mobile = window.innerWidth < 640;

    const chartEl = root.querySelector(".chart");

    const counts = {};

    for (const e of events) {
      counts[e.event] = (counts[e.event] || 0) + 1;
    }

    new chartXkcd.Pie(chartEl, {
      data: {
        labels: Object.values(LABELS).map((i) => i.label),
        datasets: [
          {
            data: Object.keys(LABELS).map((k) => counts[k] || 0),
          },
        ],
      },
      options: {
        // optional
        showLegend: !mobile,
        innerRadius: 0.5,
        legendPosition: chartXkcd.config.positionType.upRight,
        backgroundColor: "var(--background)",
        strokeColor: "var(--white)",
        dataColors: Object.values(LABELS).map((i) => i.colour),
      },
    });
  }
}
