<!--
source_url: https://partner.steamgames.com/doc/features/cloud
title: Steamworks Documentation: Steam Cloud
fetched: 2026-10-26
fetched_by: research agent for study 62b (HTML converted to plain text; navigation stripped; trimmed to the Steam Cloud article body)
-->

Steam Cloud

 Steamworks Documentation > Features > Steam Cloud 

In BriefSteam Cloud automatically stores files from your game on Steam's servers so your players can log into Steam and access their saved games from any computer.
Level of integrationConfiguration of file paths required on Steamworks website. Alternatively, API calls required from within the game code to Steamworks for the game to enumerate, read, delete, or write files to Steam Cloud.
## Steam Cloud OverviewThe Steam Cloud provides an easy and transparent remote file storage system for your game. Files specified in the Auto-Cloud configuration or written to disk (created, modified, deleted, etc.) using the Cloud API will automatically be replicated to the Steam servers after the game exits.

If the user changes computers, the files are automatically downloaded to the new computer prior to the game launching. The game can then access the files by reading them through the Cloud API or reading them directly from disk as usual. Avoid machine-specific configurations such as video settings.

The Steam Client does the work of ensuring that the files are kept synchronized across all computers the user may be accessing.

Users can globally disable Cloud synchronization in the Steam Settings under Cloud by unchecking "Enable Steam Cloud synchronization for applications which support it."

Users can also disable the Cloud synchronization on a per-game basis in each game's properties.

## Notes and Best Practices
It is important to remember that Steam will synchronize the user's Steam Cloud files for your game before and after every session. Any matching files which change during the session will be uploaded to Cloud storage immediately afterward. If your game writes very large files, or many small files, to Steam Cloud, then this may cause a noticeable impact on the user's internet bandwidth and also delay their ability to shut down Steam or re-launch the game.

As a general rule, smaller files will work better. If the saved state for a given user can be split up into different categories - things which may change frequently, and things which may not change often - then we recommend using separate files for those categories. That way, the un-changed state will not be re-uploaded after every session.
## File Size Limits
The absolute limits on file sizes for Steam Cloud may change over time. Here are some current limits and thresholds:

Size | Restriction | 
100MB | Maximum size for a call to ISteamRemoteStorage::FileWrite or ISteamRemoteStorage::FileWriteStreamWriteChunk | 
256MB | May result in a non-optimal storage endpoint choice for the user's location, negatively impacting upload/download performance | 
## Save File PathsWhen deciding where to write your save files, be sure the path will be unique for the current Steam user. If needed, you can get the user's unique Steam ID via ISteamUser::GetSteamID. From that, you can access their accountID from GetAccountID(), allowing you to have a unique variable when constructing your save path.
## Cross-Platform Saves
If your game is supported on multiple platforms - or even if you plan to support this in the future - you should consider this when setting up Steam Cloud for your game.

If you plan to read/write files directly via the ISteamRemoteStorage interface, then you can control platform sync via ISteamRemoteStorage::SetSyncPlatforms. The default for a new file is to sync to all platforms.

If you plan to use Steam Auto-Cloud, there are some key things to know. When creating new Root paths, the default OS Restriction setting is [Cross-Platform]. We strongly recommend you use this setting, even if your game currently only supports one platform. If you instead choose a specific OS, files uploaded using that rule will be "locked" to the given OS, and will not properly sync down to other platforms in the future if you try to add cross-platform support.

If your game already supports cross-platform saves, or at the time when you begin adding support for this, you will then need to define Root Overrides for the other supported platforms. Files matching a given Root path which also has platform Root Overrides will sync to all platforms in both the original Root and all Overrides. See the Steam Auto-Cloud documentation for more details.

You should only specify an OS Restriction if your game does not and will not support cross-platform saves. We recommend doing everything you can to avoid this condition, however, as it means a customer with devices across multiple platforms will never have their progress saved across those devices.
## Initial SetupTo set up Steam Cloud you must set the Byte quota per user and Number of files allowed per user options on the Steam Cloud Settings page in the Steamworks App Admin panel.

This quota is enforced on each Cloud-enabled game, on a per-user-per-game basis. It's recommended to set the values to reasonable amounts for your game title.

NOTE: Don't forget to click Save at the bottom of the page, and Publish your updated settings. Once published the cloud icon will be visible in the Steam client for anyone that owns your game.

If your game has already been released to the public then you can check the box labeled Enable cloud support for developers only. If developers-only mode is enabled then only the steam accounts which own a "Developer Comp" license for your title will see the cloud icon and will be able to use the Steam Cloud. This is useful to safely test Steam Cloud integration without breaking the public user experience. This has no effect on unreleased games since no one owns the game yet, they won't be able to see or access any cloud storage for the specific app ID.

You are able to share Cloud storage space between two app IDs by filling out the Shared cloud APP ID field. This is most commonly used to share saved games between a demo and a full game. A value of 0 disables this feature. (Note: trying to use shared cloud data with an unreleased target/base app will not sync those files and is not a recommended setup).
## Steam Cloud API and Steam Auto-CloudSteam provides two different methods of utilizing the Steam Cloud, read up on how the two methods differ, and determine which would be the best for your application.

First up is the Steam Cloud API.
The Cloud API provides a series of functions which allows you to directly integrate the Steam Cloud into your game. The Cloud API isolates individual Steam users files from each other and provides a greater level of control over the Steam Cloud.

The Steam Cloud API is exposed via the ISteamRemoteStorage API interface, and you can find example usage in the Steamworks API Example Application (SpaceWar) project.

The second is Steam Auto-Cloud.
Steam Auto-Cloud was designed for games where you choose to not integrate the Steam Cloud API. It provides a quick and easy way to get started but lacks the flexibility that is available with the Steam Cloud API.

If you prefer a deeper integration with Steam Cloud (for example, allowing to choose which save files are stored in the cloud), then you should use the Cloud API. Otherwise you can use Steam Auto-Cloud.
## Steam Auto-CloudSteam Auto-Cloud is an alternative to the Steam Cloud API that allows apps to use Steam Cloud without writing code or modifying the game in any way. It only requires that you specify the file groups which you want persisting to the Cloud. Steam will automatically sync the groups of files when the application launches and exits. Avoid machine-specific configurations such as video quality.

Note: The file steam_autocloud.vdf will be created in each location specified by your Steamworks cloud paths. This file is used by Steam, and can be ignored by your game.
## SetupAfter completing the Initial Setup the Steam Auto-Cloud configuration section will unlock on the Steam Cloud Settings page.

Root Paths describe groups of files that will be persisted to the Steam Cloud. Each Root Path can be as specific as a single file or as wide as all files under a given subfolder. Use a new path for each group of files to sync.

A Root Path is composed of 5 parts:

#### Root This is a pre-determined list of paths where game saves are commonly located.

Root | Supported OSes | Corresponding Path | 
App Install Directory | All | [Steam Install]\SteamApps\common\[Game Folder]\ | 
SteamCloudDocuments | All | Platform specific path, e.g. on Linux: ~/.SteamCloud/[username]/[Game Folder]/ | 
WinMyDocuments | Windows | %USERPROFILE%\My Documents\ | 
WinAppDataLocal | Windows | %USERPROFILE%\AppData\Local\ | 
WinAppDataLocalLow | Windows | %USERPROFILE%\AppData\LocalLow\ | 
WinAppDataRoaming | Windows | %USERPROFILE%\AppData\Roaming\ | 
WinSavedGames | Windows | %USERPROFILE%\Saved Games\ | 
MacHome | macOS | ~/ | 
MacAppSupport | macOS | ~/Library/Application Support/ | 
MacDocuments | macOS | ~/Documents/ | 
LinuxHome | Linux | ~/ | 
LinuxXdgDataHome | Linux | $XDG\_DATA\_HOME/ | 
A note regarding the Windows %USERPROFILE% paths: The corresponding paths listed above are the default locations. It is now possible for the user to configure their Windows installation so that these folders are in different locations (not necessarily under %USERPROFILE%). Steam uses the necessary Windows APIs to find the current location of these folders, whether they are default or customized.

#### Subdirectory Subdirectory path to the clouded files relative to the Root. Use `.` if there is no subdirectory.

 Auto-Cloud special path values
 Auto-Cloud allows the use of unique Steam user identifiers in the Subdirectory path. This allows you to store save files for each Steam user on the computer separately. You can use ISteamUser::GetSteamID in your game to get the current users SteamID or AccountID to save to and read from.

- {64BitSteamID} - Use this variable in the Steam path to insert the user's 64bit Steam ID. A 64 bit Steam ID looks like: 76561198027391269

- {Steam3AccountID} - Use this variable in the Steam path to insert the user's Steam3 Account ID. An Account ID looks like: 67125541
 Example: SavesDir/{64BitSteamID}

#### Pattern File mask pattern to match. You can use * as a wildcard. If you want all files in the directory, just use *.

 Example: *.sav

#### OS Restriction Sets the Operating Systems that these files will be synced from/to. This is only required if the files are OS specific, which is hopefully not the case! Otherwise, leave it at the default of Cross-Platform

#### Recursive Include sub-directories when searching for matching files. This is useful for sub-directories with non-deterministic names such as non-steam user names or IDs. If it's using a Steam ID, then using the special path values in the Subdirectory field is highly recommended.
## Root OverridesIf your application is cross-platform and requires different directories for each OS, you can use the Root Overrides functionality to specify an override for the Root Paths that you set above.

The root paths specified above can be overridden to correspond to a different path on another OS. If you use Root Overrides, you must specify [Cross-Platform] in the Root OS drop-down above.

A Root Override consists of 5 parts.

#### Original Root This corresponds to one of the Roots that you set above.

#### OS The Operating System to apply the override on.

#### New Root The new location that the Original Root maps to on the specified OS.

#### Add/Replace Path This allows you to optionally add a subdirectory path which is inserted between the new root and the original subdirectory.

#### Replace Path If enabled, it causes the path specified in Add/Replace Path to replace the original subdirectory entirely.
## Example: Configuring Auto-Cloud for Unity ApplicationsThe following is an example of setting up Auto-Cloud for use with Unity and the Application.persistentDataPath property where the value is different per OS. The Windows version is configured as the Root Path with the company in Unity set to DefaultCompany and the Project called AutocloudSample. On macOS and Linux/SteamOS, the alternate paths from Application.persistentDataPath are set in the Add/Replace Path field and Replace Path is enabled.

With these settings, Auto-Cloud files will be synchronized between the three folders as shown in the Preview samples.

## Pre-release TestingIf you are adding Steam Auto-Cloud to a game which has already been released and you have enabled developer-only mode during the Initial Setup then you must complete some additional steps to test the functionality.

- Sign in to Steam with an account that owns the app that you are testing.

- Open the Steam Console by navigating to steam://open/console in your browser.

- Enter testappcloudpaths <AppId> into the console with the given App ID that you are testing. Ex: testappcloudpaths 480

- Enter set_spew_level 4 4 into the console.

- Launch your app from Steam.

- Check the console for activity, If files already exist in the Auto-Cloud paths then you should see them being uploaded. Otherwise save some files from your app and then close it to trigger a sync.

- Go to another PC and repeat the steps above to test downloading the files from Steam Auto-Cloud.

- Be sure to test on all supported operating systems.

- Set testappcloudpaths 0 and set_spew_level 0 0 to end testing. You can restart the Steam client to get rid of the console tab.
Don't forget to disable developers-only mode and publish the changes when you're done testing.
## Dynamic Cloud Sync
Steam Cloud now supports dynamic sync - where changes appearing in the Cloud can be downloaded to the local machine during an application session. The current example is a suspended game session on the Steam Deck. For apps marked as supporting dynamic Cloud sync, Steam will synchronize files up to the Steam Cloud at the suspend time. Then, the user may run the game on another device, which will receive the updates from the Steam Deck session at launch. At exit, those changes will be uploaded to the Steam Cloud. Finally, when the Steam Deck device is awakened, Steam will synchronize the changes down to that device, and post a notification to the application that local files have changed. The application can then iterate those changes and take appropriate action. For instance, the game may be able to simply load the updated progress from disk and allow the user to pick up right where they left off on the other device. 

Check out our announcement post for even more information about why this feature exists, and how to use it. 

Note that this feature supports applications whether they use the ISteamRemoteStorage API to manage files, or Auto-Cloud.

For more details, see the ISteamRemoteStorage documentation, specifically ISteamRemoteStorage::RemoteStorageLocalFileChange_t, ISteamRemoteStorage::GetLocalFileChangeCount, and ISteamRemoteStorage::GetLocalFileChange.

