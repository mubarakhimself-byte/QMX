export const STORAGE_KEY = "qmx-factory-test-note";

export function writeNote(value: string): string {
  return value.trim();
}

export function readNote(stored: string | null): string {
  return stored ?? "";
}
