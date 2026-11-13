// One ticking clock for the whole app. Markets live in several time zones;
// every screen reads the same "now".
export type City = { id: string; name: string; zone: string; open: [number, number]; close: [number, number] };

// Cash-market hours in each city's own time. Demo defaults; the user's own
// list comes from settings later.
export const cities: City[] = [
  { id: "tok", name: "Tokyo", zone: "Asia/Tokyo", open: [9, 0], close: [15, 0] },
  { id: "lon", name: "London", zone: "Europe/London", open: [8, 0], close: [16, 30] },
  { id: "nyc", name: "New York", zone: "America/New_York", open: [9, 30], close: [16, 0] },
];

let now = $state(new Date());
if (typeof window !== "undefined") setInterval(() => (now = new Date()), 15_000);

const parts = (zone: string, d: Date) => {
  const p = new Intl.DateTimeFormat("en-GB", { timeZone: zone, hour: "2-digit", minute: "2-digit", weekday: "short", hour12: false }).formatToParts(d);
  const get = (t: string) => p.find((x) => x.type === t)?.value ?? "";
  return { h: Number(get("hour")), m: Number(get("minute")), day: get("weekday") };
};

export const clock = {
  get now() {
    return now;
  },
  time(zone: string) {
    const { h, m } = parts(zone, now);
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  },
  isOpen(c: City) {
    const { h, m, day } = parts(c.zone, now);
    if (day === "Sat" || day === "Sun") return false;
    const t = h * 60 + m;
    return t >= c.open[0] * 60 + c.open[1] && t < c.close[0] * 60 + c.close[1];
  },
  // Minutes since local midnight on this machine, for the day timeline.
  get localMinutes() {
    return now.getHours() * 60 + now.getMinutes();
  },
  // A city's open and close, shifted into this machine's local day (minutes).
  localSpan(c: City): [number, number] {
    const there = parts(c.zone, now);
    const offset = now.getHours() * 60 + now.getMinutes() - (there.h * 60 + there.m);
    const wrap = (x: number) => ((x % 1440) + 1440) % 1440;
    return [wrap(c.open[0] * 60 + c.open[1] + offset), wrap(c.close[0] * 60 + c.close[1] + offset)];
  },
};
