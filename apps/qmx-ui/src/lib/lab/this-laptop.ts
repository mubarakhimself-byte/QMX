import { ENVIRONMENTS, type Environment } from "./demo";

/**
 * This laptop as day one knows it (demo off): no model name and no specs
 * from the demo, only what the browser reports (its logical processor
 * count). The daemon will report the real hardware.
 */
export function thisLaptop(): Environment {
  const local = ENVIRONMENTS.find((e) => e.kind === "local")!;
  const threads =
    typeof navigator === "undefined" ? 0 : navigator.hardwareConcurrency;
  return {
    ...local,
    where: "",
    hardware: threads ? `${threads} threads` : "",
    status: "ready",
    slots: [0, local.slots[1]],
  };
}
