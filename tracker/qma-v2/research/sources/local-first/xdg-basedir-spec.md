<!--
source_url: https://specifications.freedesktop.org/basedir-spec/latest/  (redirects to https://specifications.freedesktop.org/basedir/latest/)
title: XDG Base Directory Specification, Version 0.8 (8 May 2021)
fetched: 2026-10-26
fetched_by: research agent for study 62b (Firecrawl markdown; normative text kept verbatim, navigation removed)
-->

# XDG Base Directory Specification (v0.8, 2021-05-08)

Authors: Waldo Bastian, Allison Karlitskaya, Lennart Poettering, Johannes Löthberg.

## 2 Basics

- There is a single base directory relative to which user-specific data files should be written. This directory is defined by the environment variable `$XDG_DATA_HOME`.
- There is a single base directory relative to which user-specific configuration files should be written. This directory is defined by the environment variable `$XDG_CONFIG_HOME`.
- There is a single base directory relative to which user-specific state data should be written. This directory is defined by the environment variable `$XDG_STATE_HOME`.
- There is a single base directory relative to which user-specific executable files may be written.
- There is a set of preference ordered base directories relative to which data files should be searched (`$XDG_DATA_DIRS`).
- There is a set of preference ordered base directories relative to which configuration files should be searched (`$XDG_CONFIG_DIRS`).
- There is a single base directory relative to which user-specific non-essential (cached) data should be written (`$XDG_CACHE_HOME`).
- There is a single base directory relative to which user-specific runtime files and other file objects should be placed (`$XDG_RUNTIME_DIR`).

All paths set in these environment variables must be absolute. If an implementation encounters a relative path in any of these variables it should consider the path invalid and ignore it.

## 3 Environment variables

- `$XDG_DATA_HOME` ... If not set or empty, a default equal to `$HOME/.local/share` should be used.
- `$XDG_CONFIG_HOME` ... default `$HOME/.config`.
- `$XDG_STATE_HOME` ... default `$HOME/.local/state`.

"The `$XDG_STATE_HOME` contains state data that should persist between (application) restarts, but that is not important or portable enough to the user that it should be stored in `$XDG_DATA_HOME`. It may contain:
- actions history (logs, history, recently used files, …)
- current state of the application that can be reused on a restart (view, layout, open files, undo history, …)"

- User-specific executable files may be stored in `$HOME/.local/bin`.
- `$XDG_DATA_DIRS` default `/usr/local/share/:/usr/share/`; `$XDG_CONFIG_DIRS` default `/etc/xdg`.
- `$XDG_CACHE_HOME` "defines the base directory relative to which user-specific non-essential data files should be stored." Default `$HOME/.cache`.
- `$XDG_RUNTIME_DIR` is for "non-essential runtime files and other file objects (such as sockets, named pipes, ...)". Mode 0700, owned by the user, bound to login session, "Files in this directory MUST not survive reboot or a full logout/login cycle." "MAY be subjected to periodic clean-up." Apps "should not place larger files in it".

## 4 Referencing this specification

- System-wide data installed to `$datadir/subdir/filename` (`/usr/share`); a user-specific version in `$XDG_DATA_HOME/subdir/filename`.
- Default configuration installed to `$sysconfdir/xdg/subdir/filename` (`/etc`); user version in `$XDG_CONFIG_HOME/subdir/filename`.
- "If, when attempting to write a file, the destination directory is non-existent an attempt should be made to create it with permission `0700`."
