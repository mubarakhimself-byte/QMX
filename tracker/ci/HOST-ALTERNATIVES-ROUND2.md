# Testing hosts without GitHub, round 2 (research, 12 November 2026)

Status: research only. I signed up for nothing and changed nothing. Sources are numbered [n] at the bottom. Round 1 is in `HOST-ALTERNATIVES.md`; this file doesn't repeat it.

**Correction to round 1.** Azure DevOps public projects are retired. New ones can't be created, and existing ones turn private in 2027 [1].

## What "his load" means here

- One full run means the whole suite on both OSes. It takes 2.5 h serially on the laptop.
- I assume about **3 vCPU-hours per OS per full run** on cloud machines. Splitting tests across more cores makes a run faster but not cheaper, because most vendors bill per vCPU-minute.
- Development phase: **20 full runs a month**, plus a QMX machine switched on for about **30 to 60 hours a month**.
- Round 1 assumed 16 shards and more setup overhead. With 1 or 2 shards per OS, as here, the bill is much smaller. If he shards more, costs go up.

## Comparison table

"Needs GitHub" = **BLOCKED** means it can't work for him while the flag stands.

| Option | Windows tests? | Linux tests? | Machine to run QMX? | UI or browser testing? | Needs GitHub? | Agent CLI | Cost for his load. Under $40? |
|---|---|---|---|---|---|---|---|
| **AWS CodeBuild** (+ CodeCommit or S3 upload) | Yes. Windows Server 2019/2022, 4 to 72 vCPU [2] | Yes. Ubuntu 24.04 and Amazon Linux [2][3] | Yes, on demand. CodeBuild "sandbox": Linux 4 vCPU $0.18/h, Windows 4 vCPU $0.40/h [4][5]. Or Lightsail fixed VMs: Windows 2 vCPU/4 GB $44/mo [6] | Playwright inside the build or sandbox. The Windows image is Server Core, so headless only. Not tested | **No.** CodeCommit takes new customers again since 25 Nov 2025 [7]. Or upload a zip of the working tree to S3 [8] | `aws codebuild start-build`, `batch-get-builds`, `start-sandbox`, `start-command-execution` [4] | **Yes.** Tests about $25 (Linux $0.60/h, Windows $1.08/h on 4 vCPU [5]). Plus $10 to $15 sandbox time. New accounts get $100 to $200 credit [9] |
| **Azure DevOps + Azure VMs** | Yes. 2 vCPU only (round 1) | Yes | Yes. VMs started and stopped by agents. Windows D2as_v5 $0.192/h, Linux $0.10/h. Windows B2als_v2 24/7 about $38/mo [10] | Yes. Hosted images carry browsers (round 1). Playwright on the VM | **No.** Azure Repos is free | `az pipelines`, `az repos`, `az vm start / stop / run-command` | **Yes on the free tier**: 1,800 min/month, 60-min jobs [1], about 10 full runs, plus VMs about $20. **No** with the $40 paid lane: about $60 total |
| **CircleCI** + GitLab Free as host | Yes. Windows medium 4 vCPU, on the Free plan too [11] | Yes | No. CI only | Playwright in jobs | Needs a host, but not GitHub: GitHub, GitLab or Bitbucket (round 1). Custom webhooks need the GitHub App [12] | `circleci` CLI and API, plus `glab` | **Yes up to about 11 runs.** Free plan gives 30,000 credits [11]. One run is about 2,700 credits. 20 runs is about $32 on Performance |
| **Codemagic** | Yes. Windows 2022, 8 vCPU / 32 GB [13] | Yes. 8 vCPU / 32 GB [14] | No. CI only | Playwright in jobs. Windows image has Python 3.9.6, so install a newer one [13] | **No.** Any git URL over HTTPS or SSH [15] | REST API: `POST /builds` [16]. No CLI for runs | **Borderline.** $0.045/min for both OSes [17]. About $2 a run, so $40 for 20 runs. Max 120 min per build [18] |
| **Buildkite** hosted agents | Yes. Windows Server 2022, Pro plan only [19][20] | Yes | No | Playwright in jobs | **No.** Any git via SSH key. Native for GitHub, Cursor Origin and Code Storage [21] | `bk build create / watch`, `bk job log`, `bk preflight` (experimental) [22] | **No.** Pro is $30/user. Windows about $29 for 20 runs. About $59 total [20] |
| **Namespace** | Windows runners GA, but for GitHub Actions only [23] | Same | Windows Devboxes in early access since 9 Nov 2026. Linux Devboxes GA [23] | — | **BLOCKED** for CI. GitLab is early access on request. Devboxes check out from GitHub or Origin [23] | `nsc`, Devbox CLI [24] | Pay as you go. Windows 4 vCPU $0.012/min [24] |
| **Depot** | Only as GitHub Actions runners. Depot CI is Linux only [25] | Yes | No | — | **BLOCKED.** Depot CI runs from GitHub, Entire or Origin repos [26] | `depot ci run` sends local changes [25] | $20/mo Developer [26] |
| **Blacksmith** | GitHub Actions runners only | Same | No | — | **BLOCKED.** GitHub organisations only [27] | — | Windows $0.008/min [28] |
| **Semaphore** | **No.** Hosted machines are Linux and macOS only [29] | Yes | No | — | No | `sem` | Out: no Windows |
| **Cirrus CI** | — | — | — | — | — | — | **Gone.** Shut down 1 June 2026 [30] |
| **Bitrise** | **No.** Managed machines are macOS and Linux [31] | Yes | No | — | No | — | Out: no Windows |
| **Harness CI** | Only if Harness Support switches it on (round 1) | Yes | No | — | No | API | Price by quote only [32]. Unclear |
| **Graphite** | Not CI. A stacked-PR and review tool, bought by Cursor in Dec 2025 [33] | — | — | — | **BLOCKED.** Built on GitHub's APIs [34] | `gt` | n/a |
| **DigitalOcean** | No Windows droplets [35]. No hosted CI | Only on your own droplet | Linux only. 2 vCPU/4 GB $24, 4/8 GB $48 [35]. App Platform is Linux only [36] | Playwright on the droplet | No | `doctl` | Linux machine only |
| **Hetzner** | No Windows images [37]. No hosted CI | Only on your own server | Linux only. CX33 (4 vCPU/8 GB) €8.99 [38]. Every plan page said "currently unavailable" on 12 Nov [38][39] | Playwright on the server | No | `hcloud` | Cheapest Linux box, if he can get one |
| **Vultr** | Windows VMs, plus a license fee per plan [40] | Only on your own VM | Yes, Windows and Linux | Playwright on the VM | No | `vultr-cli` | Not verified. Vultr's price pages blocked my reader |
| **Akamai / Linode** | No Windows image listed [41] | Only on your own VM | Linux only. 2 CPU/4 GB $24, 4/8 GB $48 [42] | Playwright on the VM | No | `linode-cli` | Linux machine only |
| **Azure Dev Box** | — | — | **Retiring.** Wind-down began 14 Sep 2026; it ends 18 Sep 2028. Needs a work account plus Windows Enterprise, Intune and Entra ID P1 licences [43] | — | No | `az` | Out |
| **Daytona** (sandbox) | Windows sandboxes, 1 to 4 vCPU [44] | Linux sandboxes | Yes, on demand. Windows 4 vCPU/16 GB about $0.80/h (my sum from [45]) | Playwright inside | No | `daytona` CLI, SDK [44] | **Gotcha:** Windows needs "Tier 3", which means a $500 top-up [46] |
| **E2B** (sandbox) | **No.** Windows not offered | Yes | Linux only. Sessions capped at 1 h (Hobby) or 24 h (Pro, $150/mo) [47] | Playwright inside | No | SDK | Out for Windows |
| **boat.dev** (sandbox) | **No.** Ubuntu only [48] | Yes | Linux only. Per-second billing; auto-stops after 1 h by default [48] | Playwright inside | No | `boat new / exec / stop / resume` [48] | Plan price not on its docs page |
| **Cua Cloud** (sandbox) | — | — | **Ended 18 Oct 2026** [49] | — | — | — | Out |
| **Browserbase** (hosted browser) | n/a | n/a | n/a | Hosted Chrome. Free: 1 browser-hour. $20/mo for 100 hours [50] | No | SDK | Only needed if Playwright can't run on the QMX machine |

Round 1 options not repeated here: GitLab Premium (Windows still beta), Cursor Origin (beta git host), Bitbucket, Codeberg, Gitea Cloud, Google.

## Can the code stay local?

- **AWS CodeBuild: yes.** An agent zips the working tree, copies it to S3, and starts a build with S3 as the source [8]. No git host at all. CodeCommit is the alternative if he wants a remote [7].
- **Codemagic: yes, with any plain git remote.** It clones from a URL over HTTPS or SSH [15].
- **Buildkite: nearly.** Any git host works with an SSH key [21]. `bk preflight` sends uncommitted changes, but via a temporary branch on that remote [22].
- **Azure Pipelines: needs a repo it knows.** Azure Repos is free, so he pushes there.
- **CircleCI: needs GitHub, GitLab, Bitbucket or Origin.** GitLab Free works as a code-only host.
- **Depot CI** can send local changes [25], but its repo must still be on GitHub, Entire or Origin [26].

## The 3 best setups

All three run hosted Windows and Linux tests, give agents a Windows and a Linux machine for QMX, use one or two CLIs, and need no GitHub.

### 1. All AWS: CodeBuild for tests, CodeBuild sandboxes for the QMX machine (about $35 to $40)

- **Tests:** CodeBuild on 4-vCPU Linux and Windows machines. Code goes up as a zip to S3, or to CodeCommit.
- **QMX machine:** a CodeBuild sandbox per OS, started on demand. Agents run commands in it and run Playwright against QMX inside it [4].
- **Cost:** tests about $25 for 20 runs, at $1.26 a run [5]. Sandboxes, 30 h per OS: about $17 [5]. Total about $40. The $100 to $200 new-account credit covers the first months [9].
- **Main gotcha:** a new account can run only **1 build at a time per machine type** until a quota raise is approved [51]. Also, the Windows build image is Server Core in a container [3]. Check that headless Chromium runs there before relying on Windows UI tests. A sandbox has no public URL, so he can't open the QMX UI himself. A Lightsail or EC2 VM fixes that, but Lightsail Windows costs $44 a month [6].
- Sandbox time costs less than build time (Windows $0.40/h against $1.08/h) [5]. Agents could run the suite in a sandbox too. It is a debugging feature, though, so treat that as a cheap extra, not the main CI.

### 2. All Azure: Azure DevOps free tier for tests, Azure VMs on demand for QMX (about $20 to $25; about $60 unlimited)

- **Tests:** Azure Pipelines on Microsoft-hosted Windows and Ubuntu. Code goes in Azure Repos (free).
- **QMX machine:** one Windows VM and one Linux VM. Agents start and stop them with `az vm`, and only pay while they run.
- **Cost:** free tier, $0 for 1,800 minutes a month [1]. That is about 10 full runs. VMs: Windows D2as_v5 at $0.192/h and Linux at $0.10/h [10], so about $18 for 60 h each, plus about $5 for two disks (round 1). Total about $23.
- **Main gotcha:** free-tier jobs stop at **60 minutes** and the month stops at 30 hours [1]. He must split each OS into 2 or more jobs, and he gets only about 10 full runs. More means buying the $40 lane, about $60 a month in total. Hosted machines are only 2 vCPU. Billing needs a real Azure subscription.
- Best if he wants one Microsoft account for code, CI, the trading node and storage.

### 3. CircleCI Free + GitLab Free + Azure VMs (about $20 to $25 for 11 runs; about $55 for 20)

- **Tests:** CircleCI Free plan, which includes Windows [11]. GitLab Free is only the code host.
- **QMX machine:** the same on-demand Azure VMs as setup 2.
- **Cost:** CI $0 for about 11 full runs (30,000 credits) [11]. VMs about $23. More runs move him to Performance: about $32 for 20 runs, about $55 in total.
- **Main gotcha:** three vendors, three logins and three tokens. When the free credits run out, builds stop until next month.

**Codemagic** is the runner-up for tests only. It takes any git URL and has big 8-vCPU machines. But about $40 for 20 runs leaves nothing for the QMX machine, and builds are capped at 120 minutes [17][18].

**Blocked while GitHub is flagged:** Namespace CI, Depot, Blacksmith and Graphite.
**Out for other reasons:** Cirrus (closed), Semaphore and Bitrise (no hosted Windows), Dev Box (retiring), Cua Cloud (closed), E2B and boat.dev (no Windows).

## Not verified

- Whether Playwright's Chromium runs in the CodeBuild Windows Server Core container. The Windows EC2 compute mode may avoid this [2].
- EC2 Windows on-demand prices. I priced Lightsail and the CodeBuild sandbox instead.
- Vultr's Windows license fee. Its pages returned 403.
- Whether Hetzner's "currently unavailable" is real or a page glitch.
- Whether AWS's new Free plan credits apply to CodeBuild.
- Namespace Windows Devbox pricing. It isn't published yet.
- AWS prices are for us-east-1. London may differ a little.

## Sources (read 12 November 2026)

1. Azure DevOps, Configure and pay for parallel jobs (updated 3 Nov 2026): https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs
2. CodeBuild compute modes and types: https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-compute-types.html
3. CodeBuild EC2 compute images: https://docs.aws.amazon.com/codebuild/latest/userguide/ec2-compute-images.html
4. CodeBuild sandbox: https://docs.aws.amazon.com/codebuild/latest/userguide/sandbox.html
5. AWS Price List API, CodeBuild us-east-1 (build-minute and sandbox-second rates): https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/CodeBuild/current/us-east-1/index.json
6. Amazon Lightsail pricing: https://aws.amazon.com/lightsail/pricing/
7. AWS CodeCommit returns to general availability: https://aws.amazon.com/blogs/devops/aws-codecommit-returns-to-general-availability and document history https://docs.aws.amazon.com/codecommit/latest/userguide/history.html
8. CodeBuild, create a build project (source providers incl. Amazon S3): https://docs.aws.amazon.com/codebuild/latest/userguide/create-project.html
9. AWS Free Tier: https://aws.amazon.com/free/
10. Azure Retail Prices API, uksouth, consumption (queried 12 Nov 2026): https://prices.azure.com/api/retail/prices
11. CircleCI pricing: https://circleci.com/pricing/
12. CircleCI custom webhooks: https://circleci.com/docs/guides/orchestrate/custom-webhooks/
13. Codemagic Windows 2022 machine: https://docs.codemagic.io/specs-windows/windows-2022/
14. Codemagic Ubuntu 24.04 machine: https://docs.codemagic.io/specs-linux/ubuntu-24.04/
15. Codemagic, adding apps: https://docs.codemagic.io/getting-started/adding-apps/
16. Codemagic REST API, builds: https://docs.codemagic.io/rest-api/builds/
17. Codemagic pricing: https://codemagic.io/pricing/
18. Codemagic build timeout: https://docs.codemagic.io/yaml-running-builds/timeout/
19. Buildkite hosted agents: https://buildkite.com/docs/pipelines/hosted-agents
20. Buildkite pricing: https://buildkite.com/pricing/
21. Buildkite hosted agents code access: https://buildkite.com/docs/pipelines/hosted-agents/code-access
22. Buildkite CLI: https://buildkite.com/docs/platform/cli
23. Namespace changelog: https://namespace.so/changelog
24. Namespace pricing: https://namespace.so/pricing and `nsc create` https://namespace.so/docs/reference/cli/create
25. Depot CI overview: https://depot.dev/docs/ci/overview
26. Depot pricing: https://depot.dev/pricing
27. Blacksmith quickstart: https://docs.blacksmith.sh/introduction/quickstart
28. Blacksmith pricing: https://www.blacksmith.sh/pricing
29. Semaphore machine types: https://docs.semaphore.io/reference/machine-types
30. Cirrus Labs announcement: https://cirruslabs.org/
31. Bitrise Q3 2026 product update: https://bitrise.io/blog/post/q3-2026-product-update
32. Harness pricing: https://www.harness.io/pricing
33. Graphite joins Cursor: https://graphite.com/blog/graphite-joins-cursor
34. Graphite docs: https://graphite.com/docs
35. DigitalOcean Droplet pricing: https://www.digitalocean.com/pricing/droplets
36. DigitalOcean App Platform limits: https://docs.digitalocean.com/products/app-platform/details/limits/
37. Hetzner Cloud servers overview: https://docs.hetzner.com/cloud/servers/overview/
38. Hetzner Cost-Optimized plans: https://www.hetzner.com/cloud/cost-optimized
39. Hetzner Regular Performance plans: https://www.hetzner.com/cloud/regular-performance
40. Vultr, is a Windows license included: https://docs.vultr.com/support/platform/billing/is-a-windows-license-included-in-the-monthly-price
41. Akamai Cloud images: https://techdocs.akamai.com/cloud-computing/docs/images
42. Akamai Cloud CPU pricing: https://www.akamai.com/cloud/pricing/cpu
43. Microsoft Dev Box quickstart (retirement notice, licences): https://learn.microsoft.com/en-us/azure/dev-box/quickstart-configure-dev-box-service
44. Daytona Windows sandboxes: https://www.daytona.io/docs/en/windows-sandboxes
45. Daytona pricing: https://www.daytona.io/pricing
46. Daytona limits and tiers: https://www.daytona.io/docs/en/limits
47. E2B pricing: https://e2b.dev/pricing
48. boat docs: https://docs.boat.dev/
49. Cua blog, Cloud Windows (notice that Cua Cloud ended 18 Oct 2026): https://cua.ai/blog/cloud-windows-ga-macos-preview
50. Browserbase pricing: https://www.browserbase.com/pricing
51. CodeBuild quotas: https://docs.aws.amazon.com/codebuild/latest/userguide/limits.html
