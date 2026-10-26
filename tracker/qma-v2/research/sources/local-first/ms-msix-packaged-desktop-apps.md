<!--
source_url: https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes
fetched_from: https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes?accept=text/markdown
title: Understanding how packaged desktop apps run on Windows (MSIX), updated 2026-09-30
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: Understanding how packaged desktop apps run on Windows - MSIX | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes
ms.subservice: msix
breadcrumb_path: /windows/msix/breadcrumb/toc.json
uhfHeaderId: MSDocsHeader-MSIX
feedback_system: Standard
feedback_product_url: https://aka.ms/msixcommunity
feedback_help_link_url: https://learn.microsoft.com/answers/tags/184/windows-app-sdk/
feedback_help_link_type: get-help-at-qna
ms.service: windows
ms.author: larryhu
author: larhu
description: This topic provides a deep dive into how the OS behaves with packaged desktop apps.
ms.date: 2026-09-30T00:00:00.0000000Z
ms.topic: concept-article
keywords: windows 11, windows 10, uwp, msix
ms.assetid: a399fae9-122c-46c4-a1dc-a1a241e5547a
locale: en-us
document_id: 8e4d8ed3-8929-6b26-24df-578abf277bb6
document_version_independent_id: 4827fb32-31b6-5329-1879-e66098c75c6d
updated_at: 2026-10-12T05:02:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/msix-pr/blob/live/msix-src/desktop/desktop-to-uwp-behind-the-scenes.md
gitcommit: https://github.com/MicrosoftDocs/msix-pr/blob/aa242ebd0732836557dd80760128c1ae4ef53c8e/msix-src/desktop/desktop-to-uwp-behind-the-scenes.md
git_commit_id: aa242ebd0732836557dd80760128c1ae4ef53c8e
site_name: Docs
depot_name: MSDN.msix
page_type: conceptual
toc_rel: ../toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.msix/{branchName}{pdfName}
word_count: 1777
asset_id: desktop/desktop-to-uwp-behind-the-scenes
moniker_range_name: 
monikers: []
item_type: Content
source_path: msix-src/desktop/desktop-to-uwp-behind-the-scenes.md
cmProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/bcbcbad5-4208-4783-8035-8481272c98b8
- https://authoring-docs-microsoft.poolparty.biz/devrel/caec7b7f-4941-4578-b79f-c63b1c1f5af4
- https://authoring-docs-microsoft.poolparty.biz/devrel/e0ffb20c-01c6-407b-a9bd-29111652a1dc
spProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/43b2e5aa-8a6d-4de2-a252-692232e5edc8
- https://authoring-docs-microsoft.poolparty.biz/devrel/754dea88-f800-4835-b6b5-280cb5d81e88
- https://authoring-docs-microsoft.poolparty.biz/devrel/3904bce4-d817-48cf-85fd-b6146fca83b7
platformId: 013f0813-8386-8365-f49d-93274ad1b9a7
---

# Understanding how packaged desktop apps run on Windows - MSIX | Microsoft Learn

This topic describes the types of desktop apps that you can create a Windows app package for, together with some operating system (OS) behaviors—and other specifics—that are important to be aware of. We'll go into details of the following items (as we'll see, the specific behavior depends on the type of your app):

- Your app's install location and working directory (which might be different from what your app has assumed in the past).
- The OS's file system and registry behavior.
- Uninstallation.

## Types of desktop app

There are two types of desktop app that you can create and package. You declare your app's type in its app package manifest by using the **uap10:RuntimeBehavior** attribute of the [Application](/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-application) element:

- One type includes both WinUI 3 apps (which use the [Windows App SDK](/en-us/windows/apps/windows-app-sdk/)) and Desktop Bridge apps (Centennial). Declared with `uap10:RuntimeBehavior="packagedClassicApp"`.
- The other type represents other kinds of Win32 app, including apps [packaged with external location](/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps). Declared with `uap10:RuntimeBehavior="win32App"`.

Universal Windows Platform (UWP) apps (`uap10:RuntimeBehavior="windowsApp"`) are also packaged; but this topic isn't about them.

And then the **uap10:TrustLevel** attribute (of the same **Application** element) determines whether or not your packaged app's process runs inside an app container.

- A *full trust* app. Declared with `uap10:TrustLevel="mediumIL"`.
- An *appContainer* app. Declared with `uap10:TrustLevel="appContainer"`. Runs in a lightweight app container. For more info, see [MSIX appContainer apps](/en-us/windows/msix/msix-container).

Important

For more details, dependencies, and capability requirements, see the documentation for those two attributes in [Application](/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-application). Also see [uap10 was introduced in Windows 10, version 2004 (10.0; Build 19041)](/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-application#uap10-was-introduced-in-windows-10-version-2004-100-build-19041).

## The purpose of packaging, and app containers

The purpose of packaging your app is to grant it *package identity* at runtime. Package identity is needed for certain Windows features (see [Features that require package identity](/en-us/windows/apps/desktop/modernize/modernize-packaged-apps)). You can package *all* combinations of app types described above (and thereby benefit from *package identity*).

But a key goal of an *appContainer* app is to separate app state from system state as much as possible, while maintaining compatibility with other apps. Windows accomplishes that by detecting and redirecting certain changes that it makes to the file system and registry at runtime (known as *virtualizing*). We'll call out when a section applies only to virtualized apps.

## Installation

App packages are installed on a per-user basis instead of system-wide. The default location for new packages on a new machine is under `C:\Program Files\WindowsApps\<package_full_name>`, with the executable named *app\_name.exe*. But packages can be installed in other places; for example, Visual Studio's **Start** commands use the project's `$(OutDir)`.

After deployment, package files are marked read-only, and are heavily locked down by the operating system (OS). Windows prevents apps from launching if those files are tampered with.

The `C:\Program Files\WindowsApps` installation store is the default [package volume](../package/package-volumes). You can create package volumes on other drives or at other paths, select a default volume, move supported packages between volumes, and take volumes offline. Not all packages are staged in a package volume; for example, Visual Studio can register a development layout directly from its build output.

## File system

The OS supports different levels of file system operations for packaged desktop apps, depending on the folder location.

### Optimized for your device

In order to avoid duplication of files (to optimize for disk storage space and reduce the bandwidth needed when downloading files), the OS leverages single storage and hard linking of files. When a user downloads an MSIX package, the `AppxManifest.xml` is used to determine whether the data contained with the package already exist on disk from an earlier package installation. If the same file exists in multiple MSIX packages, then the OS stores the shared file on disk once only, and creates hard links from both packages to the shared file. Since files are downloaded in 64Kb blocks, even if a percentage of a file being downloaded exists on disk, only the increment that's different is downloaded. That reduces the bandwidth used for downloading.

### AppData operations on Windows 10, version 1903 and later

This section applies only to virtualized apps.

All newly created files and folders in the user's `AppData` folder (for example, `C:\Users\<user_name>\AppData`) are written to a private per-user, per-app location; but merged at runtime to appear in the real `AppData` location. That allows some degree of state separation for artifacts that are used only by the app itself; which enables the system to clean up those files when the app is uninstalled.

Modifications to existing files under the user's `AppData` folder is allowed in order to provide a higher degree of compatibility and interactivity between apps and the OS. That reduces system "rot" because the OS is aware of every file or directory change made by an app. State separation also allows packaged desktop apps to pick up where an unpackaged version of the same app left off. Note that the OS doesn't support a virtual file system (VFS) folder for the user's `AppData` folder.

### AppData operations on OSes earlier than Windows 10, version 1903

This section applies only to virtualized apps.

All writes to the user's `AppData` folder (for example, `C:\Users\<user_name>\AppData`)—including create, delete, and update—are copied on write to a private per-user, per-app location. That creates the illusion that the packaged app is editing the real `AppData` when it's actually modifying a private copy. By redirecting writes that way, the system can track all file modifications made by the app. That allows the system to clean up those files when the app is uninstalled, thus reducing system "rot", and providing a better app removal experience for the user.

### Working directory, and application files

This section applies only to virtualized apps.

In addition to redirecting `AppData`, Windows' well-known folders (`System32`, `Program Files (x86)`, etc.) are dynamically merged with corresponding directories in the app package. Each package contains a folder named `VFS` at its root. Any reads of directories or files in the `VFS` directory are merged at runtime with their respective native counterparts. For example, an app could contain `C:\Program Files\WindowsApps\<package_full_name>\VFS\SystemX86\vc10.dll` as part of its app package, but the file would appear to be installed at `C:\Windows\System32\vc10.dll`. That maintains compatibility with desktop apps that expect files to live in non-package locations.

Writes to files/folders in the app package aren't allowed. Writes to files and folders that aren't part of the package are ignored by the OS, and are allowed as long as the user has permission.

### Common file system operations

This short reference table shows common file system operations and how the OS handles them.

| Operation | Result | Example |
| --- | --- | --- |
| Read or enumerate a well-known Windows file or folder | A dynamic merge of `C:\Program Files\<package_full_name>\VFS\<well_known_folder>` with the local system counterpart. | Reading `C:\Windows\System32` returns the contents of `C:\Windows\System32` plus the contents of `C:\Program Files\WindowsApps\<package_full_name>\VFS\SystemX86`. |
| Write under `AppData` | **Windows 10, version 1903 and later**: New files and folders created under the following directories are redirected to a per-user, per-package private location:<br>- Local<br>- Local\Microsoft<br>- Roaming<br>- Roaming\Microsoft<br>- Roaming\Microsoft\Windows\Start Menu\Programs<br><br>In response to a file open command, the OS will open the file from the per-user, per-package location first. If that location doesn't exist, then the OS will attempt to open the file from the real `AppData` location. If the file is opened from the real `AppData` location, then no virtualization for that file occurs. File deletes under `AppData` are allowed if user has permissions.**Earlier than Windows 10, version 1903**: Copy on write to a per-user, per-app location. | `AppData` is typically `C:\Users\<user_name>\AppData`. |
| Write inside the package | Not allowed. The package is read-only. | Writes under `C:\Program Files\WindowsApps\<package_full_name>` aren't allowed. |
| Write outside the package | Allowed if the user has permissions. | A write to `C:\Windows\System32\foo.dll` is allowed if the package doesn't contain `C:\Program Files\WindowsApps\<package_full_name>\VFS\SystemX86\foo.dll`, and the user has permissions. |

### Packaged VFS locations

This section applies only to virtualized apps.

This table shows where files shipping as part of your package are overlaid on the system for the app. Your app will perceive these files to be in the listed system locations when in fact they're in the redirected locations inside `C:\Program Files\WindowsApps\<package_full_name>\VFS`. The *FOLDERID* locations are from the [**KNOWNFOLDERID**](/en-us/windows/win32/shell/knownfolderid) constants.

| System location | Redirected location (Under [&lt;package\_root&gt;]\VFS) | Valid on architectures |
| --- | --- | --- |
| *FOLDERID\_SystemX86* | `SystemX86` | x86, amd64 |
| *FOLDERID\_System* | `SystemX64` | amd64 |
| *FOLDERID\_ProgramFilesX86* | `ProgramFilesX86` | x86, amd6 |
| *FOLDERID\_ProgramFilesX64* | `ProgramFilesX64` | amd64 |
| *FOLDERID\_ProgramFilesCommonX86* | `ProgramFilesCommonX86` | x86, amd64 |
| *FOLDERID\_ProgramFilesCommonX64* | `ProgramFilesCommonX64` | amd64 |
| *FOLDERID\_Windows* | `Windows` | x86, amd64 |
| *FOLDERID\_ProgramData* | Common `AppData` | x86, amd64 |
| *FOLDERID\_System*\catroot | `AppVSystem32Catroot` | x86, amd64 |
| *FOLDERID\_System*\catroot2 | `AppVSystem32Catroot2` | x86, amd64 |
| *FOLDERID\_System*\drivers\etc | `AppVSystem32DriversEtc` | x86, amd64 |
| *FOLDERID\_System*\driverstore | `AppVSystem32Driverstore` | x86, amd64 |
| *FOLDERID\_System*\logfiles | `AppVSystem32Logfiles` | x86, amd64 |
| *FOLDERID\_System*\spool | `AppVSystem32Spool` | x86, amd64 |

## Registry

This section (and its sub-sections) applies only to virtualized apps.

App packages contain a `registry.dat` file, which serves as the logical (virtual) equivalent of *HKLM\Software* in the real registry. At runtime, the virtual registry merges the contents of that hive into the native system hive to provide a single view of both. For example, if `registry.dat` contains a single key *Foo*, then a read of *HKLM\Software* at runtime will also appear to contain *Foo* (in addition to all the native system keys).

Although MSIX packages include *HKLM* and *HKCU* keys, they are treated differently. Only keys under *HKLM\Software* are part of the package; keys under *HKCU* or other parts of the registry are not. Writes to keys or values in the package aren't allowed. Writes to keys or values not part of the package are allowed as long as the user has permission.

All writes under *HKCU* are copied on write to a private per-user, per-app location. Traditionally, uninstallers are unable to clean *HKEY\_CURRENT\_USER* because the registry data for logged-out users is unmounted and unavailable.

All writes are kept during package upgrade, and deleted only when the app is removed entirely.

### Common registry operations

Most of this section applies only to virtualized apps.

This short reference table shows common registry operations and how the OS handles them.

| Operation | Result | Example |
| --- | --- | --- |
| Read or enumerate *HKLM\Software* | A dynamic merge of the package hive with the local system counterpart. | If `registry.dat` contains a single key *Foo*, then at runtime a read of *HKLM\Software* shows the contents of both *HKLM\Software* and *HKLM\Software\Foo*. |
| Writes under *HKCU* | Copied on write to a per-user, per-app private location. | The same as `AppData` for files. |
| Writes inside the package. | Not allowed. The package is read-only. | Writes under *HKLM\Software* aren't allowed if a corresponding key/value exist in the package hive. |
| Writes outside the package | Ignored by the OS. Allowed if the user has permissions. | Writes under *HKLM\Software* are allowed as long as a corresponding key/value doesn't exist in the package hive, and the user has the correct access permissions. |

## Uninstallation

This section applies only to virtualized apps.

When a package is uninstalled by the user, all files and folders located under `C:\Program Files\WindowsApps\<package_full_name>` are removed, as well as any redirected writes to `AppData` or the registry that were captured during the packaging process.