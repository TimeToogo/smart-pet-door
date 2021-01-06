import render from "./render.js";
import timeago from "./timeago.js";
import modal from "./modal.js";

export default class Timeline {
  static init(cfg, events) {
    console.log("init timeline...");

    const root = document.querySelector(".timeline");
    const MIN_TIME = new Date(Date.now() - 86400 * 1000);

    events = events.filter((i) => i.recordedAt > MIN_TIME);
    events = events.sort((a, b) => b.recordedAt - a.recordedAt);
    events = events.map((i) => ({
      frameUrl: i.frameUrl,
      videoUrl: i.videoUrl,
      message: Timeline.renderMessage(cfg, i),
      timeSince: timeago(i.recordedAt) + " ago",
    }));

    render(root.querySelector(".content"), [events]);

    let i = 0;
    for (const item of root.querySelectorAll("ul > li")) {
      const event = events[i];
      item.addEventListener("click", () => {
        modal.show(cfg, event);
      });
      i++;
    }
  }

  static renderMessage(cfg, e) {
    const pets = cfg.pets
      .filter((i) => e.pets.includes(i.id))
      .map((i) => i.name);
    const names =
      pets.length === 1
        ? pets[0]
        : pets.slice(0, -1).join(", ") + " & " + pets[pets.length - 1];

    const was = pets.length === 1 ? "was" : "were";

    switch (e.event) {
      case cfg.events.SIGHTING:
        return `${names} was spotted!`;

      case cfg.events.WENT_INSIDE:
        return `${names} went inside.`;

      case cfg.events.WENT_OUTSIDE:
        return `${names} went outside.`;

      case cfg.events.HUNT:
        return `${names} ${was} on the hunt!`;

      case cfg.events.FIGHT:
        return `${names} ${was} in a fight!`;

      case cfg.events.TOILET:
        return `${names} made a stinky!`;

      default:
        console.log(`Unknown event type`, e);
        return "Something happened";
    }
  }
}
