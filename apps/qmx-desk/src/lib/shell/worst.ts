// Worst-case fixture (break-ui) for the widgets that carry their own sample
// content (Usage, Settings). Card widgets and pages read his things, whose
// worst case lives in model.ts. Every value is something a real install can
// produce: long names, a server with a long host name, big counts, "Jo".
import type { Place, Row } from "./data";

const longUnit = "Gold London-open breakout with volatility filter and news guard v14-final";
const longHost = "trading-node-frankfurt-02.contabo-vps.internal";
const longSession =
  "Compare the regime study v3 against v1 on every market we have data for since 2015 and tell me which one to promote";

const stretch = (rows: Row[] | undefined, extra: Row[]): Row[] | undefined =>
  rows ? [...extra, ...rows, ...rows.map((r) => ({ ...r, label: `${r.label} (copy)` }))] : rows;

export function worst(places: Place[]): Place[] {
  return places.map((p) => ({
    ...p,
    board: p.board.map((row) =>
      row.map((panel, i) =>
        panel.kind === "card"
          ? panel
          : {
              ...panel,
              title: i === 0 ? `${panel.title}: ${longUnit}` : panel.title,
              note: panel.note && `${panel.note} · ${longHost} · since 2015-01-02 00:00 UTC`,
              rows: stretch(panel.rows, [
                { label: longSession, meta: "Approval needed before 17:30", state: "needs", where: longHost },
                { label: "Jo", state: "run" },
              ]),
              stats: panel.stats?.map((s, j) => ({
                ...s,
                value: j === 0 ? "-1,284,019.55R" : j === 1 ? "1 try" : s.value,
                label: j === 2 ? "Maximum adverse excursion at the 95th percentile" : s.label,
              })),
              table: panel.table && [
                [longUnit, ...panel.table[0].slice(1, -1), "-1,284,019.55R"],
                ...panel.table,
                ...panel.table.map((r) => [r[0], ...r.slice(1).map((c, j) => (j === 0 ? longHost : c))]),
                ["Jo", ...panel.table[0].slice(1).map(() => "")],
              ],
            },
      ),
    ),
  }));
}
