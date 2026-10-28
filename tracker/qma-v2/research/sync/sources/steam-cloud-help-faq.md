<!-- Source: https://help.steampowered.com/en/faqs/view/68D2-35AB-09A9-7678
     Fetched: 2026-10-28 through firecrawl (page is script-rendered). Excerpt of the sections used. -->

# Steam Support :: Steam Cloud (excerpt)

Intro: Steam Cloud stores game settings, save games, profile stats; many Steam client settings (collections, friend nicknames, anything changed in the client Settings menu) "will persist on an account regardless of which machine it is logged into, as the settings are pulled from the cloud upon login."

Issues: "Because of the automated nature of cloud synchronization, Steam Support has a limited ability to address issues with the cloud. If any saves or other data have been lost, it is not likely that we will be able to recover them."

## How can I enable or disable The Steam Cloud?
Toggle per game (Properties > General > Cloud Synchronization) or globally (Settings > Cloud > "Enable Steam Cloud Sync for applications that support it"). When disabled, progress is saved only locally on the machine where it was made.

## Where are cloud files stored locally?
Windows: C:\Program Files (x86)\Steam\userdata ; per Steam ID, per appID. Client settings: Steam\userdata\[steamID]\7\

## Is there a log?
Every cloud write/read is logged in cloud_log.txt (Steam\logs).

## How do I resolve a Steam Cloud conflict?
"The Steam Cloud conflict window will be shown when a game is launched, if Steam detects that the local files associated with that game differ from the ones stored on the cloud."
"Because the file was modified in two different locations without a synchronization between them, Steam cannot automatically pick which version of the file to keep."
The user is advised to usually pick the most recently modified version, after comparing the dates shown in the window. Playing in Offline Mode keeps games from syncing and is very likely to cause a conflict.

## What if Steam is unable to sync files to the cloud?
An error window; ignoring it and choosing "play game" "could potentially cause a conflict between the cloud and your local files, resulting in lost data or progress."

## Lost progress after moving machines?
Either the sync did not finish before closing, or an older version was uploaded. The original may still be on the old machine: launch Steam there so it syncs. Many games do not use Steam Cloud for saves at all.
