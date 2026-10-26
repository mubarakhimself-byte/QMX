<!--
source_url: https://learn.microsoft.com/en-us/windows/win32/msi/removefile-table
fetched_from: https://learn.microsoft.com/en-us/windows/win32/msi/removefile-table?accept=text/markdown
title: Windows Installer RemoveFile table
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: RemoveFile Table - Win32 apps | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/windows/win32/msi/removefile-table
breadcrumb_path: /windows/desktop/breadcrumb/toc.json
uhfHeaderId: MSDocsHeader-WinDevCenter
recommendations: true
adobe-target: true
ms.service: windows-api-desktop-tech
ms.subservice: installation-servicing
ms.author: jken
author: GrantMeStrength
feedback_system: Standard
feedback_product_url: https://www.microsoft.com/en-us/windowsinsider/feedbackhub/fb
feedback_help_link_url: https://learn.microsoft.com/answers/tags/224/windows-api-win32/
feedback_help_link_type: get-help-at-qna
description: The RemoveFile table contains a list of files to be removed by the RemoveFiles action. Setting the FileName column of this table to Null supports the removal of empty folders.
ms.assetid: 8b3cb0e3-ccc0-4030-8f57-aa124c3b5588
ms.topic: reference
ms.date: 2018-05-31T00:00:00.0000000Z
locale: en-us
document_id: daf0336e-5cb6-f878-6205-0ca523edfbc0
document_version_independent_id: 1f5763ce-3018-a21a-4d13-5ca8293d95b2
updated_at: 2025-03-11T21:00:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/win32-pr/blob/live/desktop-src/Msi/removefile-table.md
gitcommit: https://github.com/MicrosoftDocs/win32-pr/blob/e6437233d4a8edeec0278dc3a8a4de1e001048c0/desktop-src/Msi/removefile-table.md
git_commit_id: e6437233d4a8edeec0278dc3a8a4de1e001048c0
site_name: Docs
depot_name: MSDN.win32
page_type: conceptual
toc_rel: toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.win32/{branchName}{pdfName}
word_count: 265
asset_id: msi/removefile-table
moniker_range_name: 
monikers: []
item_type: Content
source_path: desktop-src/Msi/removefile-table.md
cmProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/caec7b7f-4941-4578-b79f-c63b1c1f5af4
- https://authoring-docs-microsoft.poolparty.biz/devrel/bcbcbad5-4208-4783-8035-8481272c98b8
spProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/754dea88-f800-4835-b6b5-280cb5d81e88
- https://authoring-docs-microsoft.poolparty.biz/devrel/43b2e5aa-8a6d-4de2-a252-692232e5edc8
platformId: daa9ce11-6c39-add5-3a49-91e4d410f587
---

# RemoveFile Table - Win32 apps | Microsoft Learn

The RemoveFile table contains a list of files to be removed by the [RemoveFiles action](removefiles-action). Setting the FileName column of this table to Null supports the removal of empty folders.

The RemoveFile table has the following columns.

| Column | Type | Key | Nullable |
| --- | --- | --- | --- |
| FileKey | [Identifier](identifier) | Y | N |
| Component\_ | [Identifier](identifier) | N | N |
| FileName | [WildCardFilename](wildcardfilename) | N | Y |
| DirProperty | [Identifier](identifier) | N | N |
| InstallMode | [Integer](integer) | N | N |

## Columns

- FileKey
    - Primary key used to identify this particular table entry.
- Component\_
    - External key the first column of the [Component table](component-table). This field references the component that controls the file to be removed.
- FileName
    - This column contains the localizable name of the file to be removed. If this column is null, then the specified folder will be removed if it is empty. All of the files that match the wildcard will be removed from the specified directory.
- DirProperty
    - Name of a property whose value is assumed to resolve to the full path to the folder of the file to be removed. The property can be the name of a directory in the [Directory table](directory-table), a property set by the [AppSearch table](appsearch-table), or any other property that represents a full path.
- InstallMode
    - Must be one of the following values.

| Constant | Hexadecimal | Decimal | Description |
| --- | --- | --- | --- |
| **msidbRemoveFileInstallModeOnInstall** | 0x001 | 1 | Remove only when the associated component is being installed (msiInstallStateLocal or msiInstallStateSource). |
| **msidbRemoveFileInstallModeOnRemove** | 0x002 | 2 | Remove only when the associated component is being removed (msiInstallStateAbsent). |
| **msidbRemoveFileInstallModeOnBoth** | 0x003 | 3 | Remove in either of the above cases. |

## Remarks

The file references in this table are processed by the [RemoveFiles action](removefiles-action).

## Validation

[ICE03](ice03)[ICE06](ice06)[ICE18](ice18)[ICE32](ice32)[ICE45](ice45)[ICE64](ice64)