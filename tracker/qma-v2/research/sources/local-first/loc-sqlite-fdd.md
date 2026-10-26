<!--
source_url: https://www.loc.gov/preservation/digital/formats/fdd/fdd000461.shtml
title: Library of Congress Sustainability of Digital Formats: SQLite Database File Format (fdd000461)
fetched: 2026-10-26
fetched_by: research agent for study 62b (HTML converted to plain text; navigation stripped)
-->

SQLite, Version 3

   | 

Digital Preservation Home | Digital Formats Home    
 | 

#  Sustainability of Digital Formats: Planning for Library of Congress Collections
 | 

 | 

 | 

 Introduction | Sustainability Factors | Content Categories | 
 Format Descriptions | Contact | 

Format Description Categories >> 
 Browse Alphabetical List

## SQLite, Version 3
 >> Back
Table of Contents

- Identification and description

- Local use

- Sustainability factors

- Quality and functionality factors

- File type signifiers

- Notes

- Format specifications

- Useful references

 Format Description Properties

- ID: fdd000461

- Short name: SQLite_3

- Content categories: 
 database, dataset

- Format Category:
 file-format

- Other facets: 
 unitary, binary, structured, symbolic

- Last significant FDD update:
 2024-05-07

- Draft status: Preliminary

### Identification and description 

 Full name | 
 SQLite, Version 3 | 

 Description | 

SQLite, version 3, is the file format used as the publicly documented native format for the SQLite database engine since June 2004. Software and associated documentation are available at https://www.sqlite.org/. The code, software, and accompanying documentation have been dedicated to the public domain. SQLite is an embedded SQL database engine that requires no configuration and reads and writes directly to ordinary disk files. A complete SQL database with tables, indexes, triggers, and views, is contained in a single disk file. The engine, and thus the file format, support a full-featured SQL implementation. The database file format, referred to here as "SQLite_3", is cross-platform, transferable between 32-bit and 64-bit systems or between big-endian and little-endian architectures. These features make SQLite_3 a popular choice as an application file format. See Adoption under Sustainability Factors below for examples of the many operating systems and software applications in which it is distributed or used.

SQLite is not directly comparable to client/server SQL database engines such as MySQL, Oracle, PostgreSQL, or SQL Server. They are designed to implement a shared repository of enterprise data; SQLite is designed to provide local data storage for individual applications. See Appropriate Uses For SQLite for more detail on when SQLite is appropriate and examples of when a client/server SQL database engine would be more appropriate.

The main SQLite_3 database file consists of one or more pages. All pages within the same database are the same size. The size of a page in bytes is a power of two between 512 and 65536 inclusive. The page size for a database file is indicated by the 2-byte integer located at an offset of 16 bytes from the beginning of the database file. The theoretical maximum size for an SQLite_3 database file is about 140 terabytes; typically, the file size limit of the underlying filesystem or hardware is the practical constraint. The smallest SQLite_3 database is a single 512-byte page.

Every page in an SQLite_3 database file is of a particular type:

- A b-tree page. The b-tree pages hold the main database content. Two kinds of b-trees are used by SQLite. The algorithm that Donald Knuth calls B*-Tree in "The Art of Computer Programming" (Volume 3, Sorting and Searching) stores all data in the leaves of the tree. SQLite calls this variety of b-tree a table b-tree. A second b-tree variant storing only keys is used in SQLite_3 and called an index b-tree. Page 1 is a table b-tree page. A 100-byte database file header is found on page 1.

- A payload overflow page. When the payload of a b-tree cell is too large for the b-tree page, the surplus is spilled onto overflow pages. Overflow pages form a linked list.

- The lock-byte page. The lock-byte page was needed to support Win95. It is not needed for modern operating systems, but is retained for backwards compatibility.

- A freelist page. A database file may contain pages that are not in active use, for example, after information is deleted from the database. The freelist is a linked list of freelist trunk pages, each of which contains page numbers for zero or more freelist leaf pages. Unused pages are stored on the freelist and reused when required. A database may be configured for vacuuming to reduce or eliminate the freelist.

- A pointer map page. These are extra pages inserted into the database to make the operation of vacuuming more efficient.

Each ordinary SQL table in the database is represented by a table b-tree. Each entry in the table b-tree corresponds to a row of the SQL table. Row data is stored as records, each with a header that indicates the data type for each value in the row, followed by a sequence of values, usually one value for each column in the table.

The first 100 bytes of the database file act as a header. Header fields include a magic number; page size in bytes; fields relating to the number of pages of various types; a code indicating the encoding used for text data (UTF-8, UTF-16le [little-endian], or UTF-16be [big-endian]); minor version number [3.x.x] for the SQLite engine used to write the database file; a code to indicate whether the database is running with write ahead logging (WAL); and codes that indicate whether the database is configured for vacuuming.
 | 

 Production phase | 
 Primarily a middle-state format, typically in active use for recording transactions. | 

 Relationship to other formats | 

     Has earlier version | 
 File formats used by SQLite version 1.0.x (initial release in August 2000) and version 2.x (initial release in September 2001), not described separately on this website at this time. | 

     Has subtype | 
 GeoPackage_1_0, 
 GeoPackage Encoding Standard (OGC), version 1.0 | 

### Local use 

 LC experience or existing holdings | 
 The Library of Congress has a small amount of SQLite files in its collections. | 

 LC preference | 
 The Library of Congress Recommended Formats Statement (RFS) includes SQLite as a preferred format for datasets. The RFS does not specify a particular version of SQLite. | 

### Sustainability factors

 Disclosure | 

Openly documented format used by the SQLite database engine. Along with all code and documentation in SQLite, the format specification has been dedicated to the public domain by its authors. Signed affidavits supporting this dedication are filed physically at Hwaci.
 | 

     Documentation | 

The SQLite file format is specified at https://www.sqlite.org/fileformat.html.
 | 

 Adoption | 

SQLite describes itself as the Most Widely Deployed and Used Database Engine. This is primarily because the SQLite database engine is distributed as part of popular operating systems, browsers, and other applications, including: Mac OS X; Linux; Windows 10; Android; iOS; Chrome; Firefox, Safari; iTunes; Dropbox; TurboTax; Skype. It is also distributed with PHP, Python, and Tcl/Tk programming languages. SQLite also has a list of Well-Known Users of SQLite.

Use of SQLite_3 as an application file format is increasing. The SQLite_3 format is the basis for the OGC's GeoPackage format, originally published in 2014. Bentley Systems, a CAD/CAM software vendor, announced in March 2013 (https://www.bentley.com/en/about-us/news/2013/march/27/navigator-mobile-app; this link was no longer working when checked in May 2022), that their new iPad app "uses the SQLite software library to deliver unmatched performance on virtually all mobile devices." SQLite_3 is used in several Apple applications, including its Mail application. Adobe Systems uses SQLite as its file format in Adobe Photoshop Lightroom. A format for mass spectrometry data based on SQLite, known as mzDB, is under development.

The SQLite Database Catalog from Filesig Software Solutions is a resource intended for digital forensics that has records for SQLite database files that may be found in a computer system or mobile device, listing filenames, signatures, likely locations and size ranges, and more. The resource lists hundreds of filenames.

A command-line utility, SQLite3, is part of the SQLite distribution and can be used from most operating systems. Other utilities permit visual browsing or forensic analysis of SQLite files. Such utilities include DB Browser for SQLite, a visual, open source tool to create, browse, search,and edit SQLite_3 files and the SQLite Viewer module from Belkasoft Evidence Center.
 | 

     Licensing and patents | 

All of the code and documentation in SQLite has been dedicated to the public domain by the authors. See https://www.sqlite.org/copyright.html.
 | 

 Transparency | 

If viewed with a text editor, the magic number and textual data, including SQL CREATE TABLE commands that define the database tables, will be visible. However, the use of the b-tree structure and binary formats for numeric data and all pointers obscures much of the data and the relationship between data records and the tables they belong to.

Note: Because SQLite is distributed with several commonly used operating systems, individuals who are technically inclined and familiar with SQL and command-line utilities may have convenient tools to hand for viewing database contents.
 | 

 Self-documentation | 

The database format incorporates technical and structural metadata needed to interpret and manipulate the data itself. For example, a database file will include the CREATE TABLE declarations that define tables and columns. To the extent that meaningful names are used for tables and columns, the nature and context of the data may be recorded. However, there is no explicit structure within the file for storing fuller descriptive and contextual metadata. Nor is there a capability to embed in the file a metadata object conforming to a schema outside the SQLite specification.

Accessibility Features

Accessibility features for datasets and databases typically involve conformance to W3C's guidelines for page structure, tables and forms. In practical terms, this means pages (if applicable to the dataset) should be well-structured with regions and headings identified and the content is marked up or tagged on a page in a way that uses appropriate and meaningful elements; tables are organized through logical relationship in grids with labeled header cells and data cells that define their relationship; and forms (if applicable to the dataset) validate input provided by the user and provide options to undo changes and confirm data entry and notify users about successful task completion, any errors, and provide instructions to help them correct mistakes. Each of these criteria should be supported by text accessible to a screen reader.

According to SQLite As An Application File Format, SQLite database content supports accessibility because "they can be viewed using a wide variety third-party tools" but this statement seems focused on portability of the data rather than support for screen readers and other digital accessibility tools. Nonetheless, SQLite is highly structured with robust metadata so, depending on implementation, SQLite has the capacity for good digital accessibility support. Comments welcome.
 | 

 External dependencies | 
 None | 

 Technical protection considerations | 
 The public domain SQLite_3 database file format described here does not support encryption. However, there is a proprietary SQLite Encryption Extension (SEE) that will encrypt the entire file and can read and write both encrypted and unencrypted files. The SEE encrypts the entire database file, both data and metadata. To an outside observer, an encrypted SQLite database file appears to be white noise. | 

### Quality and functionality factors

 Dataset | 

 Normal functionality | 
 SQLite has five classes for stored data values: NULL; INTEGER (1, 2,3, 4, or 8 bytes); REAL (8-byte floating point numbers); TEXT (length unlimited, UTF-8 or UTF-16 encodings); BLOB (binary large object). SQLite does not support built-in date and time storage classes. However, TEXT, INTEGER, or REAL can be used to store date and time values. See https://www.sqlite.org/datatype3.html and http://www.sqlitetutorial.net/sqlite-data-types/ for more detail. | 

 Support for software interfaces (APIs, etc.) | 
 There is an API for the C programming language. See C-language Interface Specification for SQLite. An interface for the Tcl scripting language exists. There is also a command line utility named sqlite3. See Command Line Shell For SQLite. | 

 Data documentation (quality, provenance, etc.) | 
 There is no built-in mechanism for recording any descriptive or contextual metadata, including information about data quality or provenance. | 

### File type signifiers and format identifiers

 Tag | 
 Value | 
 Note | 

 Filename extension | 
 db
sqlite
db3
sqlite3
 | 
 There is no file extension defined for an SQLite_3 file in its specification. The magic number (see immediately below) is the most reliable way to identify SQLite_3 files. Listed here are a number of extensions commonly found. Whether .db (or .db3) is used as opposed to the more specific .sqlite (or .sqlite3) will depend on the context. Since a user, recognizing what .sqlite meant, might be tempted to look under the hood and inadvertently change a file, .db, an extension used by several applications, is recommended by some developers. Frequently, a completely different extension is used which conveys the nature of the actual data stored, e.g., .bookmarks or .index. See What is the best extension name for SQlite database files? for various perspectives. | 

 Internet Media Type | 
 application/vnd.sqlite3
 | 
 From IANA. Registered Feb 12, 2018. | 

 Internet Media Type | 
 application/x-sqlite3

 | 
 Deprecated in favor of application/x-sqlite3. IANA registration notes: The unregistered media type "application/x-sqlite3" must not be used, except where required for backwards compatibility. | 

 Magic numbers | 
 ASCII: SQLite format 3
Hex: 53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00
 | 
 The specification requirements for database files include, "The first 16 bytes of a well-formed database file shall contain the UTF-8 encoding of the string 'SQLite format 3' followed by a single nul-terminator byte." See also GCK's File Signatures Table. | 

 Other | 
 See note. 
 | 
 NARA File Format Preservation Plan ID has no corresponding entry as of August 2024. | 

 Pronom PUID | 
 fmt/729
 | 
 See http://www.nationalarchives.gov.uk/PRONOM/fmt/729. | 

 Wikidata Title ID | 
 Q28600453
 | 
 See https://www.wikidata.org/wiki/Q28600453.
 | 

### Notes

 General | 

SQLite, as a transactional database engine, implements transactions in a way that satisfy the characteristics known as "ACID" (Atomic, Consistent, Isolated, and Durable) even if the transaction is interrupted by a system crash or power failure. Hence, although the main database file is complete, there may be subsidiary files found in the same directory. As described in Atomic Commit In SQLite, the SQLite engine supports two mechanisms to ensure that "either all database changes within a single transaction occur or none of them occur." By default, during a transaction, SQLite stores additional information in a second file called the rollback journal. Atomic Commit In SQLite provides a detailed explanation of this rollback procedure. The rollback journal is always located in the same directory as the database file and has the same name as the database file except with the 8 characters "-journal" appended. The rollback journal is usually created when a transaction is first started and is usually deleted when a transaction commits or rolls back. Starting with version 3.7.0, SQLite has supported an alternative mechanism, using a write-ahead log (WAL). The write-ahead log is stored alongside the main database file, using the same name but with the suffix "-wal". This mechanism allows to make records of the changes first in the journal and later to the database. From time to time, the information recorded to the WAL-file is transferred to the main file, this operation is called "checkpoint." If the application or host computer crashes before the transaction completes, then the rollback journal or write-ahead log contains the information needed to restore the main database file to a consistent state.
 | 

 History | 

The first official version of the SQLite database engine, version 1.0 was released in August 2000, by author D. Richard Hipp. The objective was to have an SQL database engine that required no configuration or administration and was thus suitable for embedding in other applications. See https://www.tutorialspoint.com/sqlite/sqlite_quick_guide.htm. Releases of the software are listed at History of SQLite Releases. Version 2.0 was released in September 2001 and version 3.0 in June 2004.

All releases of SQLite version 3 can read and write database files created by the first SQLite 3 release (version 3.0.0) . The developers have committed to maintaining stability, including backwards compatibility of the database file format for all future releases of SQLite 3.
 | 

### Format specifications 

- SQLite.org | Database File Format (https://www.sqlite.org/fileformat.html).

### Useful referencesURLs

- Appropriate Uses For SQLite (http://www.sqlite.org/whentouse.html). Includes examples of situations when a client-server SQL database engine might be more appropriate.

- Is using SQLite as an application file format worth it? (https://www.quora.com/Is-using-SQLite-as-an-application-file-format-worth-it). Responses recommend SQLite for saving internal data in applications.

- SQLite Version 3 Overview (https://www.sqlite.org/version3.html). Written in 2004 as a guide to programmers transitioning from SQLite2 to SQLite3

- SQLite Tutorial from Tutorials Point. (https://www.tutorialspoint.com/sqlite/).

- SQLite Quick Guide (https://www.tutorialspoint.com/sqlite/sqlite_quick_guide.htm). Includes some history.

- Forum discussions of file extensions used for SQLite_3 database files:

- Stack Overflow | What is the best extension name for SQlite database files? (http://stackoverflow.com/questions/808499/what-is-the-best-extension-name-sqlite-database-files).

- Typical suffixes of sqlite database files (link available through the Internet Archive) (https://web.archive.org/web/20210424155940/http://sqlite.1065341.n5.nabble.com/Typical-suffixes-of-sqlite-database-files-td92062.html).

- What is the difference between SQLite and Berkeley DB? (https://www.quora.com/What-is-the-difference-between-SQLite-and-Berkeley-DB).

- Mozilla Firefox 3 History File Format (https://forensicswiki.xyz/wiki/index.php?title=Mozilla_Firefox_3_History_File_Format).

- Forensic Analysis of SQLite Databases. January 31, 2017 (link available through the Internet Archive) (https://web.archive.org/web/20211011065710/http://cyberforensicator.com/2017/01/31/forensic-analysis-of-sqlite-databases/).

- GCK's File Signatures Table (https://www.garykessler.net/library/file_sigs.html).

- DB Browser for SQLite (http://sqlitebrowser.org/).

- Show SQLite tables from the Android command line shell (adb) (http://alvinalexander.com/android/android-command-line-shell-show-sqlite-tables-adb-sqlite3).

- Inspecting SQLite databases on Android and iOS (http://tonylukasavage.com/blog/2013/04/08/inspecting-sqlite-databases-on-android-and-ios/).

- How to set up and learn SQL on Mac (http://www.macworld.co.uk/how-to/mac-software/how-set-up-learn-sql-in-mac-os-x-3638150/).

- Belkasoft Evidence Center (https://belkasoft.com/ec). This forensics application includes an SQLite Viewer as an optional module.

- DB (SQLite) page from Just Solve the File Format Problem. (http://fileformats.archiveteam.org/wiki/DB_(SQLite)).

- PRONOM entry for fmt/729 (http://www.nationalarchives.gov.uk/PRONOM/fmt/729). Information in PRONOM from UK National Archives about SQLite_3. PUID: fmt/729

- mzDB: a file format using multiple indexing strategies for the efficient analysis of large LC-MS/MS and SWATH-MS data sets. By D. Bouyssié et al. March 2015. (https://www.ncbi.nlm.nih.gov/pubmed/25505153). Article describing an application file format based on SQLite for mass spectrometry data.

- Specifications of the mzDB file format. (https://github.com/mzdb/mzdb-specs). As of early 2017, the version number assigned to the current version of mzDB was 0.7.

- SQLite Database Catalog (www.filesig.co.uk/sqlitedatabasecatalog/). Catalog resource for digital forensics, listing and characterizing SQLite files that may be found in computers or mobile devices.

- SQLite Sample Database | chinook.db (http://www.sqlitetutorial.net/sqlite-sample-database/). From SQLtutorial.net

- Wikidata entry for Q28600453 (https://www.wikidata.org/wiki/Q28600453). Information in Wikidata about SQLite database file format. Wikidata Title ID: Q28600453.

Last Updated: 08/04/2025

   | 

Digital Preservation Home | Digital Formats Home    
 | 

 |
