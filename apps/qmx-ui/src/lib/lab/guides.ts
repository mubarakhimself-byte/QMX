/**
 * Copilot-led walks through the Lab. The main copilot asks a few questions,
 * then hands over one of these: each step opens a layout and says what to do
 * there. With the daemon wired, the copilot does the steps itself (skills and
 * tools) and the strip shows what it is doing.
 */
export type Guide = {
  id: string;
  title: string;
  steps: { layout: string; text: string }[];
};

export const GUIDES: Record<string, Guide> = {
  import: {
    id: "import",
    title: "Bringing in outside work",
    steps: [
      {
        layout: "build",
        text: "Import opens in the editor. Your repo becomes the bot's code; I map its functions to steps you can see.",
      },
      {
        layout: "build",
        text: "Check the inspector: anything that reads the network or the clock at run time has to be shipped inside the bot instead.",
      },
      {
        layout: "test",
        text: "First backtest on this laptop, then the same grid you used last week across the majors.",
      },
      {
        layout: "compare",
        text: "Side by side with the version you already trust. Same data, same costs, so the numbers are comparable.",
      },
    ],
  },
  train: {
    id: "train",
    title: "Training a model",
    steps: [
      {
        layout: "build",
        text: "The training workflow: dataset, features, split, leakage check, train, evaluate. Each step is editable.",
      },
      {
        layout: "train",
        text: "Training runs on the machine you picked. Curves update live; the sealed year stays closed.",
      },
      {
        layout: "compare",
        text: "Plug the model into a slot and compare the bot with and without it.",
      },
    ],
  },
  workflow: {
    id: "workflow",
    title: "A custom workflow",
    steps: [
      {
        layout: "build",
        text: "Start from an empty graph or one of your templates. Add steps from Resources, or describe them to me.",
      },
      {
        layout: "build",
        text: "Choose what starts it: a schedule, new data, a news event, or by hand. Choose where it runs.",
      },
      {
        layout: "test",
        text: "Dry-run it on recent data before it runs on its own. Then publish it.",
      },
    ],
  },
};
