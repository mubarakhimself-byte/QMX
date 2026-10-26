<!--
source_url: https://learn.microsoft.com/en-us/windows/apps/develop/data/store-and-retrieve-app-data
fetched_from: https://learn.microsoft.com/en-us/windows/apps/develop/data/store-and-retrieve-app-data?accept=text/markdown
title: Store and retrieve settings and other app data (Windows apps), updated 2026-04-18
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

---
layout: Conceptual
title: Store and retrieve settings and other app data - Windows apps | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/windows/apps/develop/data/store-and-retrieve-app-data
ms.service: windows-app-sdk
recommendations: true
ROBOTS: INDEX, FOLLOW
author: GrantMeStrength
ms.author: jken
Search.Product: eADQiWindows 10XVcnh
uhfHeaderId: MSDocsHeader-WinDevCenter
breadcrumb_path: /windows/breadcrumbs/toc.json
feedback_product_url: https://www.microsoft.com/en-us/windowsinsider/feedbackhub/fb
feedback_system: OpenSource
ms.subservice: apps
ms.update-cycle: 365-days
description: Learn how to store and retrieve local and temporary app data.
label: App settings and data
template: detail.hbs
ms.date: 2026-04-08T00:00:00.0000000Z
ms.topic: how-to
keywords: windows 11, winui
ms.localizationpriority: medium
locale: en-us
document_id: 6194f706-894c-3189-dde4-96a5a8911d55
document_version_independent_id: 6194f706-894c-3189-dde4-96a5a8911d55
updated_at: 2026-06-03T05:39:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/windows-dev-docs-pr/blob/live/hub/apps/develop/data/store-and-retrieve-app-data.md
gitcommit: https://github.com/MicrosoftDocs/windows-dev-docs-pr/blob/83397ef2eb2609b98991029731e97c4437bdda00/hub/apps/develop/data/store-and-retrieve-app-data.md
git_commit_id: 83397ef2eb2609b98991029731e97c4437bdda00
site_name: Docs
depot_name: MSDN.windows-uwp-hub
page_type: conceptual
toc_rel: ../toc.json
pdf_url_template: https://learn.microsoft.com/pdfstore/en-us/MSDN.windows-uwp-hub/{branchName}{pdfName}
feedback_help_link_type: ''
feedback_help_link_url: ''
word_count: 1763
asset_id: apps/develop/data/store-and-retrieve-app-data
moniker_range_name: 
monikers: []
item_type: Content
source_path: hub/apps/develop/data/store-and-retrieve-app-data.md
cmProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/cd440f3c-1b78-40a7-97ba-aa00a1d79df7
- https://authoring-docs-microsoft.poolparty.biz/devrel/7428317a-e6c2-4461-ad3e-8a8ad3608734
spProducts:
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/c828f7e0-89b4-459c-9bae-d7ab1c4bd9ad
- https://authoring-docs-microsoft.poolparty.biz/devrel/e4f59707-f107-48f2-8d75-0afd91868cd7
platformId: d74604fe-4b99-014d-3a70-d289566b6071
---

# Store and retrieve settings and other app data - Windows apps | Microsoft Learn

Important

The [ApplicationData](/en-us/uwp/api/Windows.Storage.ApplicationData) APIs described in this article are designed for packaged apps. Unpackaged apps do not have access to the system-managed app data stores and should use alternative storage mechanisms such as direct file I/O or registry access.

*App data* is mutable data that is created and managed by a specific app. It includes runtime state, app settings, user preferences, reference content (such as the dictionary definitions in a dictionary app), and other settings. App data is different from *user data*, data that the user creates and manages when using an app. User data includes document or media files, email or communication transcripts, or database records holding content created by the user. User data may be useful or meaningful to more than one app. Often, this is data that the user wants to manipulate or transmit as an entity independent of the app itself, such as a document.

**Important note about app data:** The lifetime of the app data is tied to the lifetime of the app. If the app is removed, all of the app data will be lost as a consequence. Don't use app data to store user data or anything that users might perceive as valuable and irreplaceable. We recommend that the user's libraries and Microsoft OneDrive be used to store this sort of information. App data is ideal for storing app-specific user preferences, settings, and favorites.

## Types of app data

There are two types of app data: settings and files.

### Settings

Use settings to store user preferences and application state info. The app data API enables you to easily create and retrieve settings (we'll show you some examples later in this article).

Here are data types you can use for app settings:

- **UInt8**, **Int16**, **UInt16**, **Int32**, **UInt32**, **Int64**, **UInt64**, **Single**, **Double**
- **Boolean**
- **Char16**, **String**
- [**DateTime**](/en-us/uwp/api/Windows.Foundation.DateTime), [**TimeSpan**](/en-us/uwp/api/Windows.Foundation.TimeSpan)
    - For C#/.NET, use: [**System.DateTimeOffset**](/en-us/dotnet/api/system.datetimeoffset?view=dotnet-uwp-10.0&amp;preserve-view=true), [**System.TimeSpan**](/en-us/dotnet/api/system.timespan?view=dotnet-uwp-10.0&amp;preserve-view=true)
- **GUID**, [**Point**](/en-us/uwp/api/Windows.Foundation.Point), [**Size**](/en-us/uwp/api/Windows.Foundation.Size), [**Rect**](/en-us/uwp/api/Windows.Foundation.Rect)
- [**ApplicationDataCompositeValue**](/en-us/uwp/api/Windows.Storage.ApplicationDataCompositeValue): A set of related app settings that must be serialized and deserialized atomically. Use composite settings to easily handle atomic updates of interdependent settings. The system ensures the integrity of composite settings during concurrent access and roaming. Composite settings are optimized for small amounts of data, and performance can be poor if you use them for large data sets.

### Files

Use files to store binary data or to enable your own, customized serialized types.

## Storing app data in the app data stores

When an app is installed, the system gives it its own per-user data stores for settings and files. You don't need to know where or how this data exists, because the system is responsible for managing the physical storage, ensuring that the data is kept isolated from other apps and other users. The system generally preserves the contents of these data stores when the user installs an update to your app, though RoamingSettings may not persist through Microsoft Store updates (see Roaming data). For settings that must survive app updates, use LocalSettings. The system removes the contents of these data stores completely and cleanly when your app is uninstalled.

Within its app data store, each app has system-defined root directories: one for local files, one for roaming files, and one for temporary files. Your app can add new files and new containers to each of these root directories.

## Local app data

Local app data should be used for any information that needs to be preserved between app sessions and is not suitable for roaming app data. Data that is not applicable on other devices should be stored here as well. There is no general size restriction on local data stored. Use the local app data store for data that it does not make sense to roam and for large data sets. Local app data reliably persists through app updates, making LocalSettings the recommended choice for user preferences and app state that must survive Microsoft Store updates.

### Retrieve the local app data store

Before you can read or write local app data, you must retrieve the local app data store. To retrieve the local app data store, use the [**ApplicationData.LocalSettings**](/en-us/uwp/api/windows.storage.applicationdata.localsettings) property to get the app's local settings as an [**ApplicationDataContainer**](/en-us/uwp/api/Windows.Storage.ApplicationDataContainer) object. Use the [**ApplicationData.LocalFolder**](/en-us/uwp/api/windows.storage.applicationdata.localfolder) property to get the files in a [**StorageFolder**](/en-us/uwp/api/Windows.Storage.StorageFolder) object. Use the [**ApplicationData.LocalCacheFolder**](/en-us/uwp/api/windows.storage.applicationdata.localcachefolder) property to get the folder in the local app data store where you can save files that are not included in backup and restore.

```CSharp
Windows.Storage.ApplicationDataContainer localSettings = 
    Windows.Storage.ApplicationData.Current.LocalSettings;
Windows.Storage.StorageFolder localFolder = 
    Windows.Storage.ApplicationData.Current.LocalFolder;
```

### Create and retrieve a simple local setting

To create or write a setting, use the [**ApplicationDataContainer.Values**](/en-us/uwp/api/windows.storage.applicationdatacontainer.values) property to access the settings in the `localSettings` container we got in the previous step. This example creates a setting named `exampleSetting`.

```CSharp
// Simple setting

localSettings.Values["exampleSetting"] = "Hello Windows";
```

To retrieve the setting, you use the same [**ApplicationDataContainer.Values**](/en-us/uwp/api/windows.storage.applicationdatacontainer.values) property that you used to create the setting. This example shows how to retrieve the setting we just created.

```CSharp
// Simple setting
Object value = localSettings.Values["exampleSetting"];
```

### Create and retrieve a local composite value

To create or write a composite value, create an [**ApplicationDataCompositeValue**](/en-us/uwp/api/Windows.Storage.ApplicationDataCompositeValue) object. This example creates a composite setting named `exampleCompositeSetting` and adds it to the `localSettings` container.

```CSharp
// Composite setting

Windows.Storage.ApplicationDataCompositeValue composite = 
    new Windows.Storage.ApplicationDataCompositeValue();
composite["intVal"] = 1;
composite["strVal"] = "string";

localSettings.Values["exampleCompositeSetting"] = composite;
```

This example shows how to retrieve the composite value we just created.

```CSharp
// Composite setting

Windows.Storage.ApplicationDataCompositeValue composite = 
   (Windows.Storage.ApplicationDataCompositeValue)localSettings.Values["exampleCompositeSetting"];

if (composite == null)
{
   // No data
}
else
{
   // Access data in composite["intVal"] and composite["strVal"]
}
```

### Create and read a local file

To create and update a file in the local app data store, use the file APIs, such as [**Windows.Storage.StorageFolder.CreateFileAsync**](/en-us/uwp/api/windows.storage.storagefolder.createfileasync) and [**Windows.Storage.FileIO.WriteTextAsync**](/en-us/uwp/api/windows.storage.fileio.writetextasync). This example creates a file named `dataFile.txt` in the `localFolder` container and writes the current date and time to the file. The **ReplaceExisting** value from the [**CreationCollisionOption**](/en-us/uwp/api/Windows.Storage.CreationCollisionOption) enumeration indicates to replace the file if it already exists.

```csharp
async void WriteTimestamp()
{
   Windows.Globalization.DateTimeFormatting.DateTimeFormatter formatter = 
       new Windows.Globalization.DateTimeFormatting.DateTimeFormatter("longtime");

   StorageFile sampleFile = await localFolder.CreateFileAsync("dataFile.txt", 
       CreationCollisionOption.ReplaceExisting);
   await FileIO.WriteTextAsync(sampleFile, formatter.Format(DateTimeOffset.Now));
}
```

To open and read a file in the local app data store, use the file APIs, such as [**Windows.Storage.StorageFolder.GetFileAsync**](/en-us/uwp/api/windows.storage.storagefolder.getfileasync), [**Windows.Storage.StorageFile.GetFileFromApplicationUriAsync**](/en-us/uwp/api/windows.storage.storagefile.getfilefromapplicationuriasync), and [**Windows.Storage.FileIO.ReadTextAsync**](/en-us/uwp/api/windows.storage.fileio.readtextasync). This example opens the `dataFile.txt` file created in the previous step and reads the date from the file. For details on loading file resources from various locations, see [How to load file resources](/en-us/previous-versions/windows/apps/hh965322%28v=win.10%29).

```csharp
async void ReadTimestamp()
{
   try
   {
      StorageFile sampleFile = await localFolder.GetFileAsync("dataFile.txt");
      String timestamp = await FileIO.ReadTextAsync(sampleFile);
      // Data is contained in timestamp
   }
   catch (Exception)
   {
      // Timestamp not found
   }
}
```

## Roaming data

Warning

Roaming data and settings is [no longer supported as of Windows 11](/en-us/windows/deployment/planning/windows-10-deprecated-features). The recommended replacement is [Azure App Service](/en-us/azure/app-service/). Azure App Service is widely supported, well documented, reliable, and supports cross-platform/cross-ecosystem scenarios such as iOS, Android and web.

Important

RoamingSettings data may not persist through Microsoft Store app updates even on Windows 10. For settings that must survive app updates, use [LocalSettings](/en-us/uwp/api/windows.storage.applicationdata.localsettings) instead.

## Temporary app data

The temporary app data store works like a cache. Its files do not roam and could be removed at any time. The System Maintenance task can automatically delete data stored at this location at any time. The user can also clear files from the temporary data store using Disk Cleanup. Temporary app data can be used for storing temporary information during an app session. There is no guarantee that this data will persist beyond the end of the app session as the system might reclaim the used space if needed. The location is available via the [**temporaryFolder**](/en-us/uwp/api/windows.storage.applicationdata.temporaryfolder) property.

### Retrieve the temporary data container

Use the [**ApplicationData.TemporaryFolder**](/en-us/uwp/api/windows.storage.applicationdata.temporaryfolder) property to get the files. The next steps use the `temporaryFolder` variable from this step.

```csharp
Windows.Storage.StorageFolder temporaryFolder = ApplicationData.Current.TemporaryFolder;
```

### Create and read temporary files

To create and update a file in the temporary app data store, use the file APIs, such as [**Windows.Storage.StorageFolder.CreateFileAsync**](/en-us/uwp/api/windows.storage.storagefolder.createfileasync) and [**Windows.Storage.FileIO.WriteTextAsync**](/en-us/uwp/api/windows.storage.fileio.writetextasync). This example creates a file named `dataFile.txt` in the `temporaryFolder` container and writes the current date and time to the file. The **ReplaceExisting** value from the [**CreationCollisionOption**](/en-us/uwp/api/Windows.Storage.CreationCollisionOption) enumeration indicates to replace the file if it already exists.

```csharp
async void WriteTimestamp()
{
   Windows.Globalization.DateTimeFormatting.DateTimeFormatter formatter = 
       new Windows.Globalization.DateTimeFormatting.DateTimeFormatter("longtime");

   StorageFile sampleFile = await temporaryFolder.CreateFileAsync("dataFile.txt", 
       CreationCollisionOption.ReplaceExisting);
   await FileIO.WriteTextAsync(sampleFile, formatter.Format(DateTimeOffset.Now));
}
```

To open and read a file in the temporary app data store, use the file APIs, such as [**Windows.Storage.StorageFolder.GetFileAsync**](/en-us/uwp/api/windows.storage.storagefolder.getfileasync), [**Windows.Storage.StorageFile.GetFileFromApplicationUriAsync**](/en-us/uwp/api/windows.storage.storagefile.getfilefromapplicationuriasync), and [**Windows.Storage.FileIO.ReadTextAsync**](/en-us/uwp/api/windows.storage.fileio.readtextasync). This example opens the `dataFile.txt` file created in the previous step and reads the date from the file. For details on loading file resources from various locations, see [How to load file resources](/en-us/previous-versions/windows/apps/hh965322%28v=win.10%29).

```csharp
async void ReadTimestamp()
{
   try
   {
      StorageFile sampleFile = await temporaryFolder.GetFileAsync("dataFile.txt");
      String timestamp = await FileIO.ReadTextAsync(sampleFile);
      // Data is contained in timestamp
   }
   catch (Exception)
   {
      // Timestamp not found
   }
}
```

## Organize app data with containers

To help you organize your app data settings and files, you create containers (represented by [**ApplicationDataContainer**](/en-us/uwp/api/Windows.Storage.ApplicationDataContainer) objects) instead of working directly with directories. You can add containers to the local, roaming, and temporary app data stores. Containers can be nested up to 32 levels deep.

To create a settings container, call the [**ApplicationDataContainer.CreateContainer**](/en-us/uwp/api/windows.storage.applicationdatacontainer.createcontainer) method. This example creates a local settings container named `exampleContainer` and adds a setting named `exampleSetting`. The **Always** value from the [**ApplicationDataCreateDisposition**](/en-us/uwp/api/Windows.Storage.ApplicationDataCreateDisposition) enumeration indicates that the container is created if it doesn't already exist.

```csharp
Windows.Storage.ApplicationDataContainer localSettings = 
    Windows.Storage.ApplicationData.Current.LocalSettings;
Windows.Storage.StorageFolder localFolder = 
    Windows.Storage.ApplicationData.Current.LocalFolder;

// Setting in a container
Windows.Storage.ApplicationDataContainer container = 
   localSettings.CreateContainer("exampleContainer", Windows.Storage.ApplicationDataCreateDisposition.Always);

if (localSettings.Containers.ContainsKey("exampleContainer"))
{
   localSettings.Containers["exampleContainer"].Values["exampleSetting"] = "Hello Windows";
}
```

## Delete app settings and containers

To delete a simple setting that your app no longer needs, use the [**ApplicationDataContainerSettings.Remove**](/en-us/uwp/api/windows.storage.applicationdatacontainersettings.remove) method. This example deletes the `exampleSetting` local setting that we created earlier.

```csharp
Windows.Storage.ApplicationDataContainer localSettings = 
    Windows.Storage.ApplicationData.Current.LocalSettings;
Windows.Storage.StorageFolder localFolder = 
    Windows.Storage.ApplicationData.Current.LocalFolder;

// Delete simple setting

localSettings.Values.Remove("exampleSetting");
```

To delete a composite setting, use the [**ApplicationDataCompositeValue.Remove**](/en-us/uwp/api/windows.storage.applicationdatacompositevalue.remove) method. This example deletes the local `exampleCompositeSetting` composite setting we created in an earlier example.

```csharp
Windows.Storage.ApplicationDataContainer localSettings = 
    Windows.Storage.ApplicationData.Current.LocalSettings;
Windows.Storage.StorageFolder localFolder = 
    Windows.Storage.ApplicationData.Current.LocalFolder;

// Delete composite setting

localSettings.Values.Remove("exampleCompositeSetting");
```

To delete a container, call the [**ApplicationDataContainer.DeleteContainer**](/en-us/uwp/api/windows.storage.applicationdatacontainer.deletecontainer) method. This example deletes the local `exampleContainer` settings container we created earlier.

```csharp
Windows.Storage.ApplicationDataContainer localSettings = 
    Windows.Storage.ApplicationData.Current.LocalSettings;
Windows.Storage.StorageFolder localFolder = 
    Windows.Storage.ApplicationData.Current.LocalFolder;

// Delete container

localSettings.DeleteContainer("exampleContainer");
```

## Versioning your app data

You can optionally version the app data for your app. This would enable you to create a future version of your app that changes the format of its app data without causing compatibility problems with the previous version of your app. The app checks the version of the app data in the data store, and if the version is less than the version the app expects, the app should update the app data to the new format and update the version. For more info, see the [**ApplicationData.Version**](/en-us/uwp/api/windows.storage.applicationdata.version) property and the [**ApplicationData.SetVersionAsync**](/en-us/uwp/api/windows.storage.applicationdata.setversionasync) method.