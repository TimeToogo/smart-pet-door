import api from "./api.js";
import timeline from "./timeline.js";
import latestSightings from "./latestSightings.js";
import inVsOut from "./inVsOut.js";
import frequencies from "./frequencies.js";
import modal from "./modal.js";

const init = async () => {
  console.log("initialising app...");

  const cfg = window.PetConfig;
  const events = await api.getEvents(
    new Date(Date.now() - 30 * 24 * 3600 * 1000)
  );

  timeline.init(cfg, events);
  latestSightings.init(cfg, events);
  inVsOut.init(cfg, events);
  frequencies.init(cfg, events);
  modal.init(cfg);
};

init();
