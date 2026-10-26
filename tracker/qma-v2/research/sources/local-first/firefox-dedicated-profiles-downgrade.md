<!--
source_url: https://support.mozilla.org/en-US/kb/dedicated-profiles-firefox-installation
title: Mozilla Support: Dedicated profiles per Firefox installation (last updated 2026-04-14)
fetched: 2026-10-26
fetched_by: research agent for study 62b (Firecrawl markdown, trimmed; images removed)
-->

# Dedicated profiles per Firefox installation

## What are profiles?
"Firefox saves information such as bookmarks, passwords and user preferences in a set of files called a profile. This profile is stored in a location separate from the Firefox application files."

## What happens if I have more than one installation of Firefox?
"Firefox uses a dedicated profile for each installation of Firefox, including Nightly, Beta, Developer Edition and Extended Support Release (ESR) installations. This makes Firefox more stable when switching between installations on the same computer, and also allows you to run different Firefox installations at the same time."
"If you install a new, additional installation of Firefox, a new profile will be created. You will not lose the personal data or customizations you had before, since your old profile data is saved and associated with the previous Firefox installation."

## Can I change which Firefox installation uses a previous profile?
"Yes. You can use the Profile Manager for each installation, to set a new default profile."

## What happens to my profile if I downgrade to a previous version of Firefox?
"You'll have to create a new profile to avoid corruption issues."
"Starting with Firefox version 67, each Firefox installation requires a separate profile."
"If you try to launch a Firefox installation with a profile that was last used in a more recent version, you'll see a warning that using an older version of Firefox can corrupt profile data such as bookmarks and browsing history." ... "Click the Create New Profile button to start Firefox with a new profile."
"When you downgrade Firefox and use a new profile, any profile that was used in the higher version is still available in the Profile Manager, for use in a more recent version of Firefox."
"Note: Downgrade protection can be overridden when you launch Firefox through the command line using the --allow-downgrade parameter. Alternatively, you can open the Firefox profile folder for the profile you wish to use and delete (or rename) the compatibility.ini file."
