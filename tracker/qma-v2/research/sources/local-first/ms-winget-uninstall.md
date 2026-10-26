<!--
source_url: https://learn.microsoft.com/en-us/windows/package-manager/winget/uninstall
fetched_from: https://learn.microsoft.com/en-us/windows/package-manager/winget/uninstall?accept=text/markdown
title: winget uninstall command
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: '`uninstall` Command | Microsoft Learn'
canonicalUrl: https://learn.microsoft.com/en-us/windows/package-manager/winget/uninstall
ms.service: dev-environment
recommendations: true
ROBOTS: INDEX, FOLLOW
author: GrantMeStrength
ms.author: jken
Search.Product: eADQiWindows 10XVcnh
uhfHeaderId: MSDocsHeader-Windows-DevTools
breadcrumb_path: /windows/breadcrumbs/toc.json
feedback_product_url: https://github.com/microsoft/winget-cli/issues
feedback_system: OpenSource
ms.subservice: package-manager
ms.update-cycle: 365-days
description: Uninstalls the specified application.
ms.date: 2026-07-19T00:00:00.0000000Z
ms.topic: overview
locale: en-us
document_id: e38a4717-5dc9-ceaa-f023-ba7bf7657b71
document_version_independent_id: d81c530e-f9ad-612f-1c56-0114d9097124
updated_at: 2026-07-21T05:03:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/windows-dev-docs-pr/blob/live/hub/package-manager/winget/uninstall.md
gitcommit: https://github.com/MicrosoftDocs/windows-dev-docs-pr/blob/866cea8f1d9b8bd9defb17041a075e3822ca2c06/hub/package-manager/winget/uninstall.md
git_commit_id: 866cea8f1d9b8bd9defb17041a075e3822ca2c06
site_name: Docs
depot_name: MSDN.windows-uwp-hub
page_type: conceptual
toc_rel: ../toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.windows-uwp-hub/{branchName}{pdfName}
feedback_help_link_type: ''
feedback_help_link_url: ''
word_count: 661
asset_id: package-manager/winget/uninstall
moniker_range_name: 
monikers: []
item_type: Content
source_path: hub/package-manager/winget/uninstall.md
cmProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/12ed19f9-ebdf-4c8a-8bcd-7a681836774d
- https://authoring-docs-microsoft.poolparty.biz/devrel/bcbcbad5-4208-4783-8035-8481272c98b8
spProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/3a764584-4f97-452b-8f1d-36f19b12f6ae
- https://authoring-docs-microsoft.poolparty.biz/devrel/43b2e5aa-8a6d-4de2-a252-692232e5edc8
platformId: 43708d86-8c48-2912-639c-3f316462c469
---

# `uninstall` Command | Microsoft Learn

The **`uninstall`** command of [`winget`](./) uninstalls the specified application.

The **`uninstall`** command requires that you specify the exact application name to uninstall. If there is any ambiguity, you will be prompted to further filter the **`uninstall`** command to an exact application.

## Aliases

The following aliases are available for this command:

- `remove`
- `rm`

## Usage

```cmd
winget uninstall [[-q] <query>] [<options>]
```

[![Screenshot of entering the winget uninstall command in a command line of Windows Terminal.](images/uninstall.png)](images/uninstall.png#lightbox)

Note

When using WinGet to uninstall a package, you may encounter a Microsoft Store agreement. This happens because of how WinGet queries package sources. To avoid Microsoft Store agreement prompts when uninstalling, you can add the `--source winget` WinGet flag to the `winget uninstall` command. Alternatively, you can uninstall using **Start &gt; Settings &gt; Apps &gt; Apps & features**, finding the app you want to remove, and selecting **More &gt; Uninstall**.

## Arguments

The following arguments are available.

| Argument | Description |
| --- | --- |
| **`-q`, `--query`** | The query used to search for an app. |

Note

The query argument is positional. Wild-card style syntax is not supported. This is most often the string of characters you expect to help find the package you are uninstalling.

## Options

The options allow you to customize the uninstall experience to meet your needs.

| Option | Description |
| --- | --- |
| **`-m`, `--manifest`** | Must be followed by the path to the manifest (YAML) file. You can use the manifest to run the uninstall experience from a [local YAML file](install#local-install). |
| **`--id`** | Limits the uninstall to the ID of the application. |
| **`--name`** | Limits the search to the name of the application. |
| **`--moniker`** | Limits the search to the moniker listed for the application. |
| **`--product-code`** | Filters using the product code. |
| **`-v`, `--version`** | Enables you to specify an exact version to uninstall. If not specified, latest will uninstall the highest versioned application. |
| **`--all`, `--all-versions`** | Uninstall all versions. |
| **`-s`, `--source`** | Restricts the search to the source name provided. Must be followed by the source name. |
| **`-e`, `--exact`** | Uses the exact string in the query, including checking for case-sensitivity. It will not use the default behavior of a substring. |
| **`--scope`** | Select installed package scope filter (user or machine). |
| **`-i`, `--interactive`** | Runs the uninstaller in interactive mode. The default experience shows uninstaller progress. |
| **`-h`, `--silent`** | Runs the uninstaller in silent mode. This suppresses all UI. The default experience shows uninstaller progress. |
| **`--force`** | Direct run the command and continue with non security related issues. |
| **`--purge`** | Deletes all files and directories in the package directory (portable). |
| **`--preserve`** | Retains all files and directories created by the package (portable). |
| **`-o`, `--log`** | Directs the logging to a log file. You must provide a path to a file that you have the write rights to. |
| **`--header`** | Optional Windows-Package-Manager REST source HTTP header. |
| **`--authentication-mode`** | Specify authentication window preference (silent, silentPreferred or interactive). |
| **`--authentication-account`** | Specify the account to be used for authentication. |
| **`--accept-source-agreements`** | Used to accept the source license agreement, and avoid the prompt. |
| **`-?`, `--help`** | Shows help about the selected command. |
| **`--wait`** | Prompts the user to press any key before exiting. |
| **`--logs`, `--open-logs`** | Open the default logs location. |
| **`--verbose`, `--verbose-logs`** | Used to override the logging setting and create a verbose log. |
| **`--nowarn`, `--ignore-warnings`** | Suppresses warning outputs. |
| **`--disable-interactivity`** | Disable interactive prompts. |
| **`--proxy`** | Set a proxy to use for this execution. |
| **`--no-proxy`** | Disable the use of proxy for this execution. |

After you have successfully identified the application intended to uninstall, winget will execute the uninstall command.

### Example queries

The following example uninstalls a specific version of an application.

```cmd
winget uninstall --name powertoys --version 0.15.2
```

The following example uninstalls an application using its ID.

```cmd
winget uninstall --id "{24559D0F-481C-F3BE-8DD0-D908923A38F8}"
```

The following example uninstalls multiple applications.

```cmd
winget uninstall Microsoft.NuGet Microsoft.Edit
```

## Multiple selections

If the query provided to **winget** does not result in a single application to uninstall, then **winget** will display multiple results. You can then use additional filters to refine the search for the application you want to uninstall.

## Uninstalling apps not installed with Windows Package Manager

As mentioned in [**`list`**](list), the **winget list** command will display more than just apps installed with the **winget**. You may still use winget commands to remove these apps from your device.