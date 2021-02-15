const CACHE_KEY = "petdoor:events";

const clear = () => {
  localStorage.removeItem(CACHE_KEY);
};

const get = () => {
  try {
    const events = localStorage.getItem(CACHE_KEY)
      ? JSON.parse(localStorage.getItem(CACHE_KEY))
      : [];

    console.log(`retrieved ${events.length} events from cache...`);
    return events.map(preRevive);
  } catch (e) {
    console.error("error while retrieving from cache");
    return [];
  }
};

const preRevive = (event) => ({
  ...event,
  recordedAt: new Date(event.recordedAt),
});

const set = (events) => {
  console.log(`saving ${events.length} events to cache...`);
  localStorage.setItem(CACHE_KEY, JSON.stringify(events.map(prePersist)));
};

const prePersist = (event) => ({
  ...event,
  recordedAt: recordedAt.toISOString(),
});

export default { get, set, clear };
