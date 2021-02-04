export default class Api {
  static async getEvents(sinceDate) {
    console.log("fetching events...");

    const events = await fetch(`/api/events?since=${sinceDate.toISOString()}`)
      .then((r) => r.json())
      .then((r) =>
        r.events.map((e) => ({
          pets: e.pets,
          event: e.event,
          videoUrl: e.videoUrl,
          frameUrl: e.frameUrl,
          recordedAt: new Date(e.recordedAt),
        }))
      );

    return events;
  }
}
