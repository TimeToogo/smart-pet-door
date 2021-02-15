import api from "./api.js";
import cache from "./cache.js"
import timeline from "./timeline.js";
import latestSightings from "./latestSightings.js";
import inVsOut from "./inVsOut.js";
import frequencies from "./frequencies.js";
import modal from "./modal.js";

const init = async () => {
  console.log("initialising app...");

  const cfg = window.PetConfig;

  if (window.location.search.includes('cache=clear')) {
    cache.clear()
  }

  let events = cache.get()

  let latestEventDate = events.length
   ? new Date(Math.max(...events.map(i => i.recordedAt.getTime())) + 1000)
   : new Date(Date.now() - 30 * 24 * 3600 * 1000);

  events = events.concat(await api.getEvents(latestEventDate))

  cache.set(events)

  timeline.init(cfg, events);
  latestSightings.init(cfg, events);
  inVsOut.init(cfg, events);
  frequencies.init(cfg, events);
  modal.init(cfg);
};

init();
