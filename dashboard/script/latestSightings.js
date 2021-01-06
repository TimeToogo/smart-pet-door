import render from "./render.js";
import timeago from "./timeago.js";

export default class LatestSightings {
  static init(cfg, events) {
    console.log("init latest sightings...");

    const root = document.querySelector(".sightings");

    // sort by most recent
    events = events.sort((a, b) => b.recordedAt - a.recordedAt);

    const sightings = cfg.pets
      .map((pet) => {
        const event = events.find((i) => i.pets.includes(pet.id));

        if (!event) {
          return null;
        }

        return {
          pet: pet.name,
          videoUrl: event.videoUrl,
          timeSince: timeago(event.recordedAt) + ' ago',
        };
      })
      .filter((i) => !!i);

    render(root.querySelector(".content"), [sightings]);
  }
}
