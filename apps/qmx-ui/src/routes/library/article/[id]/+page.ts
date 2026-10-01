// Article ids come from the Library at runtime, so this route is not prerendered.
export const prerender = false;

export function load({ params }) {
  return { id: params.id };
}
