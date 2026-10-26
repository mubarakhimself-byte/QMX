<!--
source_url: https://www.sqlite.org/pragma.html
title: SQLite PRAGMA statements (user_version, application_id)
fetched: 2026-10-26
fetched_by: research agent for study 62b (HTML converted to plain text; navigation stripped; trimmed to the application_id and user_version entries)
-->

PRAGMA schema.application_id;

PRAGMA schema.application_id = integer ;

The application_id PRAGMA is used to query or set the 32-bit
 signed big-endian "Application ID" integer located at offset
 68 into the database header. Applications that use SQLite as their
 application file-format should set the Application ID integer to
 a unique integer so that utilities such as 
 file(1) can determine the specific
 file type rather than just reporting "SQLite3 Database". A list of
 assigned application IDs can be seen by consulting the
 magic.txt file in the SQLite source repository.

 See also the user_version pragma.

...

PRAGMA schema.user_version;

PRAGMA schema.user_version = integer ;

 The user_version pragma will get or set
 the value of the user-version integer at offset 60 in the
 database header. The user-version is an integer that is
 available to applications to use however they want. SQLite
 makes no use of the user-version itself.

 See also the application_id pragma and schema_version pragma.

 