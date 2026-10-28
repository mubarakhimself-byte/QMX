<!-- Source: https://chromium.googlesource.com/chromium/src/+/main/components/sync/base/data_type.h
     Fetched: 2026-10-28. Excerpt (lines 30-215: the DataType enum with its comments), verbatim. -->

```cpp
  // a) The client received *valid* data from a data type which this version
  // is unaware of (only present in versions newer than this one, or present
  // in older versions but removed since).
  // b) The client received invalid data from the server due to some error.
  // c) A data object was just created, in which case this is a temporary state.
  UNSPECIFIED,

  // ------------------------------------ Start of "real" data types.
  // The data types declared before here are somewhat special, as they
  // they do not correspond to any browser data model.  The remaining types
  // are bona fide data types; all have a related browser data model and
  // can be represented in the protocol using a specific Message type in the
  // EntitySpecifics protocol buffer.
  //
  // A bookmark folder or a bookmark URL object.
  BOOKMARKS,
  FIRST_USER_DATA_TYPE = BOOKMARKS,  // Declared 2nd, for debugger prettiness.
  FIRST_REAL_DATA_TYPE = FIRST_USER_DATA_TYPE,

  // A preference object, a.k.a. "Settings".
  PREFERENCES,
  // A password object.
  PASSWORDS,
  // An autofill_profile object, i.e. an address.
  AUTOFILL_PROFILE,
  // An autofill object, i.e. an autocomplete entry keyed to an HTML form field.
  AUTOFILL,
  // Credentials related to an autofill wallet instrument; aka the CVC/CVV code.
  AUTOFILL_WALLET_CREDENTIAL,
  // Credit cards and customer data from the user's account. These are read-only
  // on the client.
  AUTOFILL_WALLET_DATA,
  // Usage counts and last use dates for Wallet cards. This data is both
  // readable and writable.
  AUTOFILL_WALLET_METADATA,
  // Autofill usage data of a payment method related to a specific merchant.
  AUTOFILL_WALLET_USAGE,
  // A theme object.
  THEMES,
  // An extension object.
  EXTENSIONS,
  // An object representing a custom search engine.
  SEARCH_ENGINES,
  // An object representing a browser session, e.g. an open tab. This is used
  // for "Open Tabs".
  SESSIONS,
  // An app object.
  APPS,
  // An app setting from the extension settings API.
  APP_SETTINGS,
  // An extension setting from the extension settings API.
  EXTENSION_SETTINGS,
  // History delete directives, used to propagate history deletions (e.g. based
  // on a time range).
  HISTORY_DELETE_DIRECTIVES,
  // Custom spelling dictionary entries.
  DICTIONARY,
  // Client-specific metadata, synced before other user types.
  DEVICE_INFO,
  // These preferences are synced before other user types and are never
  // encrypted.
  PRIORITY_PREFERENCES,
  // Family Link supervised user settings. Cannot be encrypted.
  SUPERVISED_USER_SETTINGS,
  // App List items, used by the ChromeOS app launcher.
  APP_LIST,
  // ARC package items, i.e. Android apps on ChromeOS.
  ARC_PACKAGE,
  // Printer device information. ChromeOS only.
  PRINTERS,
  // Reading list items.
  READING_LIST,
  // Commit only user events.
  USER_EVENTS,
  // Commit only user consents.
  USER_CONSENTS,
  // Tabs sent between devices.
  SEND_TAB_TO_SELF,
  // Commit only security events.
  SECURITY_EVENTS,
  // Wi-Fi network configurations + credentials
  WIFI_CONFIGURATIONS,
  // A web app object.
  WEB_APPS,
  // OS-specific preferences (a.k.a. "OS settings"). ChromeOS only.
  OS_PREFERENCES,
  // Synced before other user types. Never encrypted. ChromeOS only.
  OS_PRIORITY_PREFERENCES,
  // Commit only sharing message object.
  SHARING_MESSAGE,
  // A workspace desk saved by user. ChromeOS only.
  WORKSPACE_DESK,
  // Synced history. An entity roughly corresponds to a navigation.
  HISTORY,
  // Trusted Authorization Servers for printers. ChromeOS only.
  PRINTERS_AUTHORIZATION_SERVERS,
  // Contact information from the Google Address Storage.
  CONTACT_INFO,
  // A tab group saved by a user. Currently only supported on desktop platforms
  // (Linux, Mac, Windows, ChromeOS) and Android.
  SAVED_TAB_GROUP,

  // WebAuthn credentials, more commonly known as passkeys.
  WEBAUTHN_CREDENTIAL,

  // Invitations for sending passwords. Outgoing invitation from one user will
  // become an incoming one for another.
  INCOMING_PASSWORD_SHARING_INVITATION,
  OUTGOING_PASSWORD_SHARING_INVITATION,

  // Data related to tab group sharing.
  SHARED_TAB_GROUP_DATA,

  // Special datatype to notify client about People Group changes. Read-only on
  // the client.
  COLLABORATION_GROUP,

  // Product comparison groups.
  PRODUCT_COMPARISON,

  // Browser cookies, ChromeOS only.
  COOKIES,

  // Valuables stored in the Google Wallet.
  // Read-only on the client.
  AUTOFILL_VALUABLE,

  // Account-local metadata for shared tab groups.
  SHARED_TAB_GROUP_ACCOUNT_DATA,

  // Comments for shared contexts.
  SHARED_COMMENT,

  // ACCOUNT_SETTING(s) forwarded from the user's account. Since the
  // settings originate from the user account, this is not reusing any of the
  // standard syncable prefs.
  // Read-only on the client.
  ACCOUNT_SETTING,

  // A user thread when interacting with AI features.
  AI_THREAD,

  // Information about a contextual task.
  CONTEXTUAL_TASK,

  // Usage metadata for `AUTOFILL_VALUABLE`.
  AUTOFILL_VALUABLE_METADATA,

  // A skill that the user has saved.
  SKILL,

  // A gemini thread.
  GEMINI_THREAD,

  // A theme object specifically for iOS devices.
  THEMES_IOS,

  // A theme object specifically for Android devices.
  THEMES_ANDROID,

  // Encrypted tab context container.
  ENCRYPTED_TAB_CONTEXT_CONTAINER,

  // Encrypted tab context item.
  ENCRYPTED_TAB_CONTEXT_ITEM,

  // Information about a notebook.
  NOTEBOOK,

  // Information about a history journey.
  JOURNEY,

  // User entity suppression records for Autofill AI.
  AUTOFILL_ENTITY_SUPPRESSION,

  LAST_USER_DATA_TYPE = AUTOFILL_ENTITY_SUPPRESSION,

  // ---- Control Types ----
  // An object representing a set of Nigori keys.
  NIGORI,
  LAST_REAL_DATA_TYPE = NIGORI,

  // NEW ENTRIES MUST BE ADDED ABOVE THIS.
  LAST_ENTRY = LAST_REAL_DATA_TYPE,
};

```
