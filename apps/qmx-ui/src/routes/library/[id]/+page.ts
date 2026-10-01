import { DEMO_ENTITIES } from "$lib/demo/assets";

// Entity ids come from the daemon at runtime, so this route is not prerendered.
export const prerender = false;

export function load({ params }) {
  return {
    id: params.id,
    entity: DEMO_ENTITIES.find((e) => e.id === params.id) ?? null,
  };
}
