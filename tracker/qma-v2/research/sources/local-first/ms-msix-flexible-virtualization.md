<!--
source_url: https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization
fetched_from: https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization?accept=text/markdown
title: MSIX flexible virtualization
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: Flexible virtualization - MSIX | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization
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
description: The flexible virtualization feature provides a way for your app to declare that *some set* of its files and Registry entries should be visible to other apps; and that those should persist on app uninstall. *All other* files and Registry entries are not visible to other apps; and are removed on uninstall.
ms.date: 2021-10-20T00:00:00.0000000Z
ms.topic: article
keywords: windows 10, uwp, msix, flexible, virtualization
locale: en-us
document_id: ade2a380-92b4-08d3-eeaf-66d440c599bd
document_version_independent_id: ade2a380-92b4-08d3-eeaf-66d440c599bd
updated_at: 2026-01-28T20:56:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/msix-pr/blob/live/msix-src/desktop/flexible-virtualization.md
gitcommit: https://github.com/MicrosoftDocs/msix-pr/blob/d2ffe67361996e17296e727ad07e1d57b09b27d1/msix-src/desktop/flexible-virtualization.md
git_commit_id: d2ffe67361996e17296e727ad07e1d57b09b27d1
site_name: Docs
depot_name: MSDN.msix
page_type: conceptual
toc_rel: ../toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.msix/{branchName}{pdfName}
word_count: 1215
asset_id: desktop/flexible-virtualization
moniker_range_name: 
monikers: []
item_type: Content
source_path: msix-src/desktop/flexible-virtualization.md
cmProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/19ec6774-09b8-473e-a17e-b17b518bbad7
- https://authoring-docs-microsoft.poolparty.biz/devrel/bcbcbad5-4208-4783-8035-8481272c98b8
- https://authoring-docs-microsoft.poolparty.biz/devrel/caec7b7f-4941-4578-b79f-c63b1c1f5af4
spProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/ade36b61-c646-4bd8-87ee-f3a843461962
- https://authoring-docs-microsoft.poolparty.biz/devrel/43b2e5aa-8a6d-4de2-a252-692232e5edc8
- https://authoring-docs-microsoft.poolparty.biz/devrel/754dea88-f800-4835-b6b5-280cb5d81e88
platformId: a67becc1-085c-4995-f693-cf36ff56220b
---

# Flexible virtualization - MSIX | Microsoft Learn

## Overview

The flexible virtualization feature provides a way for your app to declare that *some set* of its files and Registry entries should be visible to other apps; and that those should persist on app uninstall. *All other* files and Registry entries are *not* visible to other apps; and are removed on uninstall.

## How to control the virtualization of selected locations

Note

The behavior described in this section was introduced in Windows 11.

Starting from Windows 11, the system retains the existing behavior of the [**unvirtualizedResources**](/en-us/windows/uwp/packaging/app-capability-declarations#restricted-capabilities) restricted capability, and the [**RegistryWriteVirtualization**](/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-desktop6-registrywritevirtualization) and [**FilesystemWriteVirtualization**](/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-desktop6-filesystemwritevirtualization) properties. In addition, the system adds the ability for your app to declare specific folders and/or Registry keys that you want to be unvirtualized.

- You can declare only file system locations that are within `%USERPROFILE%\AppData`.
- You can declare only Registry locations that are within **HKCU**.

Here's an example.

```xml
<!-- Declare the desktop6 and/or virtualization XML namespace where the virtualization properties are defined, and include this in the list of ignorable namespaces. -->
<!-- Declare the XML namespace for the required restricted capability, and include it in the list of ignorable namespaces. -->
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:desktop6="http://schemas.microsoft.com/appx/manifest/desktop/windows10/6"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  xmlns:virtualization="http://schemas.microsoft.com/appx/manifest/virtualization/windows10"
  IgnorableNamespaces="rescap desktop6 virtualization">

  <!-- ... -->
  <!-- Other entries omitted for brevity. -->
  <!-- ... -->

  <Properties>
    <!-- If you don't want virtualization of registry writes to HKEY_CURRENT_USER, then include the property, and set it to disabled. -->
    <desktop6:RegistryWriteVirtualization>disabled</desktop6:RegistryWriteVirtualization>

    <!-- If you don't want virtualization of file system writes to the user's AppData folder, then include the property, and set it to disabled. -->
    <desktop6:FileSystemWriteVirtualization>disabled</desktop6:FileSystemWriteVirtualization>
    
    <!-- On Windows 11 and later OS versions, you can declare specific file system and/or registry locations that you want to be unvirtualized. 
    If these are recognized on the current device, then they take precedence over the old declarations. On older devices,
    the new declarations are ignored and the old ones are honored. -->
    <virtualization:FileSystemWriteVirtualization>
      <virtualization:ExcludedDirectories>
        <virtualization:ExcludedDirectory>$(KnownFolder:LocalAppData)\Fabrikam\Widgets</virtualization:ExcludedDirectory>
        <virtualization:ExcludedDirectory>$(KnownFolder:RoamingAppData)\Fabrikam\Widgets</virtualization:ExcludedDirectory>
      </virtualization:ExcludedDirectories>
    </virtualization:FileSystemWriteVirtualization>

    <virtualization:RegistryWriteVirtualization>
      <virtualization:ExcludedKeys>
        <virtualization:ExcludedKey>HKEY_CURRENT_USER\Software\Fabrikam\Widgets</virtualization:ExcludedKey>
      </virtualization:ExcludedKeys>
    </virtualization:RegistryWriteVirtualization>
  </Properties>

  <Capabilities>
    <!-- Include the required restricted capability. -->
    <rescap:Capability Name="unvirtualizedResources"/>
  </Capabilities>
</Package>
```

Note

If your app declares both the pre-Windows 11 and the Windows 11 syntax, then the old declaration will be used on pre-Windows 11 versions, while the new declaration will be used on pre-Windows 11 and later.

## Mechanisms prior to Windows 11

In traditional environments, apps can create, update, and delete files in most places in the file system. And they can create, update, and delete entries in the Windows Registry. Those files and Registry entries are visible to other apps on the system, even though they often don't need to be. In addition, when the app is uninstalled, those files and Registry entries are often left behind, and become clutter.

In the Universal Windows Platform (UWP), such files and Registry entries are virtualized so that only the app that writes them can see them. And they're removed when the app is uninstalled. But there are valid scenarios where the app wants such files and Registry entries to be visible to other apps. In addition, other apps might require that those files and entries persist even after the app that wrote them is uninstalled.

### Default MSIX behavior

| Location | Context | Description |
| --- | --- | --- |
| **HKCU** | Install-time | - The app can include a `user.dat` file that specifies **HKCU**\**Software** entries. These entries are actually written to a `user.dat` file in the user's **AppData** folder (in a sub-folder for each app), and presented to the app as if the keys were in **HKCU**.<br>- For reading, this private hive is merged with the unvirtualized **HKCU**\**Software** so that all entries appear to be in the same place.<br>- When the app is uninstalled, the virtualized entries are no longer available, because they were never actually added to the registry.<br>- Keys in the virtualized hive are visible only to the app. |
| **HKCU** | Run-time | - Writes go to a separate per-app, per-user private hive.<br>- For reading, this hive is merged with the unvirtualized HKCU so that all entries appear to be in the same place.<br>- When the app is uninstalled, the virtualized entries are removed.<br>- Keys in the virtualized hive are only visible to the app. |
| **HKLM** | Install-time | - The app can include a `registry.dat` file that specifies **HKLM**\**Software** entries. These entries are actually written to a `user.dat` file in the user's **AppData** folder (in a sub-folder for each app), and presented to the app as if the keys were in **HKLM**.<br>- For reading, this private hive is merged with the unvirtualized **HKLM**\**Software** so that all entries appear to be in the same place.<br>- When the app is uninstalled, the virtualized entries are no longer available, because they were never actually added to the registry.<br>- Keys in the virtualized hive are visible only to the app. |
| **HKLM** | Run-time | - Writes under **HKLM** are allowed as long as a corresponding key/value doesn't exist in the package hive and the user has the correct access permissions (which effectively means this is only available to a Centennial app running elevated). |
| **Well-known folders** | Install-time | - The app can include a *VFS* folder with well-known named subfolders that contain arbitrary files.<br>- For reading, these subfolders are merged with the unvirtualized well-known locations, so that all files appear to be in the same place. |
| **AppData** | Run-time | - For Windows versions less than or equal to 1809, all writes to the user's **AppData** folder (including create, delete, and update) are copied on write to a private per-user, per-app location, which is merged at run-time to appear in the real **AppData** location.<br>- For Windows versions greater than 1809, all newly created files and folders in the user's **AppData** folder are written to a private per-user, per-app location which is merged at run-time to appear in the real **AppData** location. Modifications to existing **AppData** files is done on the unvirtualized files. For reads, the system tries the private location first, then falls back to the unvirtualized **AppData**.<br>- On fallback, writes to the unvirtualized files are allowed.<br>- When the app is uninstalled, the virtualized entries are removed.<br>- Files in the virtualized location are visible only to the app.<br>- There's no VFS support for **AppData**.<br>- Apart from **AppData**, the app can write to any location where the user has write access, including other parts of `%userprofile%` (of which **AppData** is just one part). |

### The `unvirtualizedResources` restricted capability

Note

Support for the `unvirtualizedResources` restricted capability was introduced in Windows 10, version 1903 (10.0; Build 18362), also known as the Windows 10 May 2019 Update.

Your app can declare the `unvirtualizedResources` restricted capability, and set the **RegistryWriteVirtualization** and/or **FilesystemWriteVirtualization** properties to `true`, to get write access to **HKCU** and/or to **AppData**. This is to enable the case where your app needs to write entries that are then visible to other processes outside of its package. For example, games write save data to **AppData**, and that data needs to persist even after the game is uninstalled.

| Property | Description |
| --- | --- |
| **RegistryWriteVirtualization=disabled** | Writes to **HKCU** go to the unvirtualized location, are visible to other processes outside the package, and are not cleaned up on app uninstall. |
| **FilesystemWriteVirtualization=disabled** | Writes to **AppData** go to the unvirtualized location, are visible to other processes outside the package, and are not cleaned up on app uninstall. |

This mechanism turns off **HKCU** and/or **AppData** virtualization altogether, which goes against the primary goal. It's not a fine-grained tool, and it often exceeds the requirements of a given app.