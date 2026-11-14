# Where to move QMX off GitHub (research, 12 November 2026)

Status: research only. I signed up for nothing and changed nothing. Prices come from vendor pages and the Azure retail price API, read on 12 November 2026. Sources are at the bottom, numbered [n].

## What we need

- One place that hosts the code (git, branches, pull or merge requests, branch protection) and runs CI on **hosted** Linux and **hosted** Windows machines. No self-hosted runners.
- About 16 jobs at once (8 shards per OS).
- An agent-drivable CLI or API, like `gh`: open a PR, read its checks, merge.
- Easy import of a full mirror: 387 branches and 24 tags in the local clone, about 125 MB.
- Load: one user, about 16 parallel jobs, 200 to 400 CI hours a month across both OSes.

**What the load means.** One full run is roughly 2.5 h serial × 2 OSes, plus slower 2-vCPU cloud machines and setup per shard. That comes to about 8 job-hours per run, so 200 to 400 hours is about 25 to 50 full runs a month. In the cost figures below I assume half Linux and half Windows.

## Comparison table

| Option | Hosts code? | Hosted Windows? | Hosted Linux? | 16 parallel jobs? | Agent CLI | Monthly cost for his load | Migration effort |
|---|---|---|---|---|---|---|---|
| **Azure DevOps** (Repos + Pipelines) | Yes. Free for up to 5 users [3] | **Yes, GA.** Windows Server 2022/2025 images [4] | Yes. Ubuntu 24.04/26.04 [4] | Yes. Buy 16 Microsoft-hosted parallel jobs. New orgs can have up to 25 [2] | `az repos pr create / show / update --status completed / --auto-complete`, `az repos pr policy list` for checks [12] | **$640 flat** (16 × $40, unlimited minutes) [3]. $320 if he accepts 8 jobs and runs the shards in two waves | Medium. Mirror push in minutes [13]. Rewrite the 6 workflows as `azure-pipelines.yml`. Swap `gh` for `az` in agent tooling |
| **GitLab.com Premium** | Yes. Protected branches on every tier [9] | **Yes, but beta**, with no SLA [5][6] | Yes. GA, 2 to 32 vCPU [7] | No published cap. Usage is metered by minutes [8] | `glab mr create / view / merge`, `glab ci status`, `glab api` [11] | **About $49 to $169**: $29 seat [1], 10,000 minutes included, extra at $10 per 1,000 [1]. Small Linux and Windows both count 1× [8]. About $290 if Linux runs on 4-vCPU machines (2×) | Medium. `git push --mirror`, a `.gitlab-ci.yml` rewrite, `gh` → `glab` (the closest match to `gh`) |
| **CircleCI Performance + a host** (GitLab Free or Bitbucket) | No. CI only; supports GitHub, GitLab and Bitbucket [14] | Yes. Windows medium is 4 vCPU/16 GB [15] | Yes [15] | Yes. Up to 80 concurrent [14] | `circleci` CLI plus the host's CLI (`glab`) | **About $165 to $345**: $15 per 25,000 credits; Linux 10 credits/min, Windows 40 credits/min [14][15]. GitLab Free host: $0 | Medium to high. Two vendors, two configs, two tokens |
| Cursor **Origin** (the "Casa/Carsa Origin" he remembers) | Yes, in **early beta** since 17 Aug 2026 [16]. Needs Cursor Premium ($30/mo) or higher [17] | Only through a CI app (for example CircleCI) [18] | Through a CI app [18] | Depends on the CI app | `origin pr create` / merge, `origin ruleset` [19]. I could not confirm a checks command | $30 plus the CI app (about $165 to $345 with CircleCI) | High and risky. Early beta; the docs don't say whether the CLI runs on Windows |
| Bitbucket Cloud | Yes [20] | **No.** Windows runners are self-hosted only [21] | Yes (Cloud Runner) [21] | n/a | Not checked | Out | — |
| Codeberg (Forgejo / Woodpecker) | Yes | **No.** Woodpecker is `linux/amd64` only; Forgejo Actions is in "open alpha"; access by application [22] | Limited | No | — | Out | — |
| Gitea Cloud | Yes | **Not stated.** Says it has managed runners; no OS or minutes listed [23] | Not stated [23] | Not stated | `tea` [23] | No published price [24] | Unknown |
| Harness (CI + Code Repository) | Yes | Yes, but Windows must be switched on by Harness Support [25] | Yes [25] | Up to 60 concurrent on Essentials [26] | API | **Sales quote only** [26]. Free plan: 2,000 credits [25] | Not one-click |
| Google (Secure Source Manager + Cloud Build) | Only via Secure Source Manager, at **$1,000/month per instance** [27]. Cloud Source Repositories closed to new users on 17 June 2024 [28] | **No hosted Windows.** Only an experimental community builder that creates Windows VMs [29] | Yes (Cloud Build) | — | `gcloud` | $1,000+ | Out on price and Windows |
| AWS CodeCatalyst | — | — | — | — | — | **Closed to new customers** [30] | Out |
| SourceHut | Yes | **No.** Linux and BSD images only [31] | Yes | — | — | Out | — |
| Buildkite | No (CI only) | I did not verify hosted Windows | — | — | — | Not researched further. CI only, and the brief expected it to need his own agents | — |
| Replit | **No.** It is a browser IDE with a Git pane that pushes to GitHub or other hosts [32] | No | No | — | — | Not a fit | — |

## Recommendation

### 1. Azure DevOps (Azure Repos + Azure Pipelines)

Why:
- It is the only option where hosted Windows **and** hosted Linux are both generally available, with one flat price and no minute counting. 16 parallel jobs cost $640 a month, and each job may run up to 6 hours [2][3].
- The machine images come from the same `actions/runner-images` project that GitHub Actions uses [4]. The Windows and Ubuntu machines the old workflows expected are essentially the same.
- Repos, branch policies (build validation as a required check) and PRs are free for up to 5 users [3]. Import is one click, or `git push --mirror` [13].
- `az repos pr` covers create, auto-complete when checks pass, and complete (merge) [12]. That is enough for agents.
- It fits his wider wish for one cloud (see the last section).

Gotchas:
- Every machine has 2 vCPU, 7 GB RAM and about 10 GB free disk, and it can't be made bigger [4]. Expect each shard to run slower than on the laptop. Keep shards well under the 6-hour cap.
- The 16 jobs are shared by every pipeline in the organisation [2]. One full run takes all 16, and a second push waits in the queue.
- Billing needs a normal Azure subscription. Azure DevOps doesn't support the Azure Free Trial [10]. I could not confirm that the Azure for Students credit pays for parallel jobs, so plan on pay-as-you-go.
- YAML syntax differs from GitHub Actions, so the 6 workflows need rewriting. Marketplace `uses:` actions don't carry over.
- Sign up with a Microsoft account or university account, **not "Sign in with GitHub"**, so the flagged GitHub identity isn't involved.

### 2. GitLab.com Premium

Why:
- It is by far the cheapest: about $49 to $169 a month for his load [1][8].
- `glab` is the closest thing to `gh` [11], and the import is a mirror push.
- Big Linux machines (up to 32 vCPU) are available if the Linux shards need speed [7].

Gotchas:
- **Hosted Windows is still beta**, with no SLA. New Windows VMs take about 5 minutes to start, jobs may wait longer in the queue, and the fleet can go down for maintenance [5][6]. With 8 Windows shards on every run, that is the weak spot.
- Windows comes in one size only, 2 vCPU / 7.5 GB, with PowerShell and no Docker `image:` [5].
- Every hosted job is hard-capped at 3 hours [6].
- Premium is billed annually ($348 up front) [1].
- If Windows beta proves flaky, keep GitLab as the host and run the Windows shards on CircleCI (Windows medium, 4 vCPU). That adds roughly $145 to $290 a month [14][15].

Runner-up note: CircleCI + GitLab Free works and has strong Windows machines, but it means two vendors and two configs, for about the same money as option 2 plus the Windows fix.

## The two names he wasn't sure of

- **"Casa/Carsa Origin" is Cursor's Origin.** It is git hosting from the Cursor AI editor company, in early beta since 17 August 2026. It comes with Cursor Premium ($30/mo) and above, not Free or Plus [16][17]. It has repos, PRs, rulesets and a CLI [19]. **It has no CI of its own.** CI comes from marketplace apps (Buildkite, CircleCI, Depot, Namespace, RWX and others), and those apps only work on repos hosted on Origin, not on repos mirrored from GitHub [18]. Too new for a 10,300-test, two-OS gate.
- **Replit** is a browser IDE and app builder. It uses Git but pushes to GitHub, GitLab or Bitbucket; it is not a git host with CI [32]. Not a fit.

## Side notes

**Opening a new GitHub account.** GitHub's Terms say: "One person or legal entity may maintain no more than one free Account" (Section B.3) [33]. A second free account would break that rule. The Terms have no clause naming suspension evasion. But GitHub "reserves the right to refuse service to anyone for any reason at any time" (Section M.3) [33]. The Acceptable Use Policies ban "fake accounts" and give GitHub "full discretion" to act [34]. In practice, a second account would likely be linked to the flagged one and suspended too. Not recommended.

**Does `gh` tooling need replacing?** Yes. `gh` only talks to GitHub. The in-repo scripts on `main` don't call `gh` (I searched them). The `gh` calls live in the agent skills and prompts (coordinator, `ship land`, PR checks, merges), and those need the new CLI:
- Azure DevOps: `az repos pr create`, `az repos pr policy list` (check status), `az repos pr update --status completed` or `--auto-complete true` (merge) [12], plus `az pipelines` for runs.
- GitLab: `glab mr create`, `glab ci status` / `glab mr view`, `glab mr merge` [11].

**Mirror gotcha.** If the local clone is the only full copy, push its remote-tracking refs as branches, not just local branches:

```
git push <new> 'refs/remotes/origin/*:refs/heads/*'
git push <new> --tags
```

Alternatively, `git clone --mirror` from GitHub first, since he can still read his own repo with his token.

## One cloud for everything?

He leans to Azure because QMX also needs: a small VM running a trading node 24/7, object storage like the current Cloudflare R2 buckets, and external compute. Azure against Google on that wider fit:

| Need | Azure | Google Cloud |
|---|---|---|
| Code hosting | Azure Repos, free for 5 users [3] | Secure Source Manager only, **$1,000/month** [27]. The old Cloud Source Repositories is closed to new users [28] |
| Hosted CI, Linux + Windows | Azure Pipelines, $40 per parallel job [3] | Cloud Build is Linux. Windows only through a community builder that creates VMs [29] |
| Small Linux VM, 24/7 (pay as you go) | UK South [35]: **B2als v2** (2 vCPU, 4 GiB) $0.0425/h ≈ **$31/mo**. B2ats v2 (2 vCPU, 1 GiB) ≈ $7.70/mo. B1ms (1 vCPU, 2 GiB) ≈ $17/mo. Plus a 32 GiB Standard SSD (E4) at $2.64/mo [35] | **e2-small** (2 shared vCPU, 2 GB) $0.01675/h ≈ **$12/mo** list price [36]. One e2-micro is free in 3 US regions [37] |
| Object storage | Blob Hot LRS, UK South: $0.0192 per GB-month, writes $0.059 per 10k, reads $0.0047 per 10k. Internet egress: first 100 GB free, then about $0.087/GB [35] | Standard: from $0.020 per GiB-month, varying by region. 5 GB free in US regions only [37][38] |
| For comparison: Cloudflare R2 | $0.015 per GB-month, **no egress fees**, 10 GB free [39] | same |
| Student offer | **Azure for Students:** $100 credit for 12 months, no card, renewable yearly. Full-time students only, with the school email [40] | $300 / 90-day Free Trial for anyone, card required [37]. Student "education credits" (about $50) come only through a course lecturer [41] |

**Recommendation: Azure, one account for code, CI and the trading node.**
- Google can't host his code at a sane price ($1,000/month), and it has no hosted Windows CI. That alone rules it out as the "one cloud".
- Google's small VM is cheaper (about $12 against about $31 a month for a 2-vCPU box). That saving is small next to the CI bill, and Azure has a UK region.
- **Keep R2 for buckets that are read from outside Azure** (the laptop, other compute). R2 is cheaper per GB and has zero egress [39].
- Use Azure Blob only for data mostly read by Azure machines.
- Mixing is fine. R2 speaks the S3 API, so nothing forces a move.

**Student offers.**
- Azure for Students ($100) is worth claiming, but **check eligibility**: it says full-time only [40], and many University of London programmes are distance or part-time.
- $100 covers the trading VM for about 3 months. It does not cover CI.
- Google's student credits need a lecturer to request them [41].
- The GitHub Student Developer Pack needs a working GitHub account, so it is moot while the flag stands.

## Sources (read 12 November 2026)

1. GitLab pricing: https://about.gitlab.com/pricing/
2. Azure DevOps, Configure and pay for parallel jobs (updated 3 Nov 2026): https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs
3. Azure DevOps Services pricing: https://azure.microsoft.com/en-us/pricing/details/devops/azure-devops-services/
4. Microsoft-hosted agents (updated 9 Nov 2026): https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted
5. GitLab, Hosted runners on Windows: https://docs.gitlab.com/ci/runners/hosted_runners/windows/
6. GitLab-hosted runners (3-hour timeout, beta not under SLA): https://docs.gitlab.com/ci/runners/hosted_runners/
7. GitLab, Hosted runners on Linux: https://docs.gitlab.com/ci/runners/hosted_runners/linux/
8. GitLab, Compute minutes and cost factors: https://docs.gitlab.com/ci/pipelines/compute_minutes/
9. GitLab, Protected branches: https://docs.gitlab.com/user/project/repository/branches/protected/
10. Azure DevOps, Manage billing (no Free Trial support): https://learn.microsoft.com/en-us/azure/devops/organizations/billing/set-up-billing-for-your-organization-vs
11. GitLab CLI `glab mr`: https://docs.gitlab.com/cli/mr/ and https://docs.gitlab.com/cli/
12. Azure CLI `az repos pr`: https://learn.microsoft.com/en-us/cli/azure/repos/pr
13. Import a Git repo into Azure Repos: https://learn.microsoft.com/en-us/azure/devops/repos/git/import-git-repository
14. CircleCI pricing: https://circleci.com/pricing/
15. CircleCI resource classes: https://circleci.com/product/features/resource-classes/
16. Cursor changelog, Origin Code Hosting (17 Aug 2026): https://cursor.com/changelog/origin-code-hosting
17. Cursor pricing: https://cursor.com/pricing
18. Cursor Origin apps: https://cursor.com/docs/origin/apps
19. Origin CLI commands: https://cursor.com/docs/origin/cli/reference/commands
20. Bitbucket pricing: https://www.atlassian.com/software/bitbucket/pricing
21. Bitbucket runners comparison: https://support.atlassian.com/bitbucket-cloud/kb/bitbucket-runners-comparison/
22. Codeberg CI docs: https://docs.codeberg.org/ci/
23. Gitea Cloud: https://about.gitea.com/products/cloud
24. Gitea pricing: https://about.gitea.com/pricing
25. Harness Cloud build infrastructure: https://developer.harness.io/docs/continuous-integration/use-ci/set-up-build-infrastructure/use-harness-cloud-build-infrastructure
26. Harness pricing: https://www.harness.io/pricing
27. Secure Source Manager pricing: https://cloud.google.com/products/secure-source-manager/pricing and https://cloud.google.com/products/secure-source-manager
28. Cloud Source Repositories release notes (end of sale 17 June 2024): https://docs.cloud.google.com/source-repositories/docs/release-notes
29. Cloud Build community windows-builder: https://github.com/GoogleCloudPlatform/cloud-builders-community/blob/master/windows-builder/README.md
30. Amazon CodeCatalyst user guide: https://docs.aws.amazon.com/codecatalyst/latest/userguide/welcome.html
31. builds.sr.ht compatibility: https://man.sr.ht/builds.sr.ht/compatibility.md
32. Replit version control: https://docs.replit.com/learn/projects-and-artifacts/version-control
33. GitHub Terms of Service: https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
34. GitHub Acceptable Use Policies: https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
35. Azure Retail Prices API, region `uksouth`, USD consumption prices (queried 12 Nov 2026): https://prices.azure.com/api/retail/prices
36. Google Compute Engine general-purpose VM pricing: https://cloud.google.com/products/compute/pricing/general-purpose
37. Google Cloud Free Program: https://docs.cloud.google.com/free/docs/free-cloud-features
38. Google Cloud Storage pricing: https://cloud.google.com/storage/pricing and https://cloud.google.com/storage
39. Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
40. Azure for Students: https://azure.microsoft.com/en-us/free/students
41. Google Cloud education credits: https://docs.cloud.google.com/billing/docs/how-to/edu-grants

**Not verified:**
- GitLab's hosted-runner concurrency cap. It isn't published, and the Windows beta queue is the risk.
- Gitea Cloud runner OS and prices. Not published.
- Whether Azure for Students credit can pay for Azure DevOps parallel jobs.
- The exact London price of Google's VM and storage. Google's pages load prices by script; the e2-small figure is the default list rate.
- Buildkite hosted Windows.
