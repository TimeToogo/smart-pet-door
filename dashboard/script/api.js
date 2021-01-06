export default class Api {
    static async getEvents(sinceDate) {
        console.log('fetching events...')
        // TODO: build and integrate API

        await new Promise(res => setTimeout(res, 100));

        // Mock events
        const cfg = window.PetConfig;
        const NUM_EVENTS = 1000;
        const events = [];
        let prevDate = new Date()

        for (let i = 0; i < NUM_EVENTS; i++) {
            const petRandom = Math.random();
            let pets;

            if (petRandom < 0.1) {
                pets = cfg.pets.map(i => i.id)
            } else if (petRandom < 0.55) {
                pets = [cfg.pets[0].id]
            } else {
                pets = [cfg.pets[1].id]
            }

            const event = Math.ceil((Object.keys(cfg.events).length - 1) * Math.random())
            const recordedAt = new Date()
            recordedAt.setTime(prevDate.getTime() - 7200 * 1000 * Math.random())
            const videoUrl = '/static/sample-video.mp4';
            const frameUrl = '/static/sample-frame.png';

            events.push({
                pets, event, videoUrl, frameUrl, recordedAt
            })

            prevDate = recordedAt
        }

        return events
    }
}