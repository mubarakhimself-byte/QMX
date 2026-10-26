<!--
source_url: https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data
title: Mozilla Support: Profiles - Where Firefox stores your bookmarks, passwords and other user data (last updated 2026-07-19)
fetched: 2026-10-26
fetched_by: research agent for study 62b (Firecrawl markdown, trimmed to the relevant parts; images and per-Windows-version click paths removed)
-->

# Profiles - Where Firefox stores your bookmarks, passwords and other user data

"All of the changes you make in Firefox, such as your home page, what toolbars you use, extensions you have installed, saved passwords and your bookmarks, are stored in a special folder called a _profile_. Your profile folder is stored in a separate place from the Firefox program so, if something ever goes wrong with Firefox, your data and settings will still be there. It also means that you can uninstall Firefox without losing your personal information and that you don't have to reinstall Firefox to clear your settings or troubleshoot a problem."

## Finding your profile without opening Firefox

Default location on Windows: `C:\Users\<your Windows login username>\AppData\Roaming\Mozilla\Firefox\Profiles\` (that is, `%APPDATA%\Mozilla\Firefox\Profiles\`).

"The MSIX (Microsoft Store) Firefox version stores its profiles in a different location": `%LOCALAPPDATA%\Packages\Mozilla.Firefox...\LocalCache\Roaming\Mozilla\Firefox\Profiles\`.

macOS: `~/Library/Application Support/Firefox/Profiles/`. Linux (Ubuntu): `~/.mozilla/firefox/`.

The profile location is shown in about:support ("Profile Folder" with an Open Folder button).

## What information is stored in my profile? (partial list from the page)

- `places.sqlite` (bookmarks, downloads, history); `bookmarkbackups` folder ("bookmark backup files, which can be used to restore your bookmarks"); `favicons.sqlite`
- `key4.db`, `logins.json` (passwords)
- `permissions.sqlite`, `content-prefs.sqlite`
- `search.json.mozlz4`, `persdict.dat`, `formhistory.sqlite`, `cookies.sqlite`, `webappsstore.sqlite`
- `extensions` folder, `cert9.db`, `pkcs11.txt`, `handlers.json`
- `sessionstore.jsonlz4` (open tabs and windows), `xulstore.json` (window positions)
- `prefs.js` (user preferences; an optional `user.js` overrides), `containers.json`

## Working with profiles (linked articles)

- Manage Firefox profiles; Profile Manager (create, remove or switch profiles, "which can also be accessed when Firefox is closed").
- "Recover user data missing after Firefox update or reinstall".
- "Manually back up and restore Firefox profile data ... also explains how to move your profile information to a different location on your hard drive or to another computer."
