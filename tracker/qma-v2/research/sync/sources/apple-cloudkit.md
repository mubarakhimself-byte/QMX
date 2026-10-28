<!-- Source: https://developer.apple.com/documentation/cloudkit
     Fetched: 2026-10-28 via the page's documentation JSON (https://developer.apple.com/tutorials/data/documentation/cloudkit.json); text extracted. -->

# CloudKit
Store structured app and user data in iCloud containers that all users of your app can share.

## Overview
The CloudKit framework provides interfaces for moving data between your app and your iCloud containers. You use CloudKit to store your app’s existing data in the cloud so that the user can access it on multiple devices. You can also store data in a public area where all users can access it.

## Using the CloudKit framework
CloudKit isn’t a replacement for your app’s existing data objects. Instead, CloudKit provides complementary services for managing the transfer of data to and from iCloud servers. Because it provides minimal offline caching support, CloudKit relies on the presence of the network and, optionally, a valid iCloud account. A valid iCloud account is only necessary when you want to save data that is specific to a single user. Apps can always store data in a public area that is readable by all users.
Records are at the heart of all data transactions in CloudKit. A record is a dictionary of key-value pairs that represents the data you want to save. You can add new keys and values to records at any time, and you can create links between related records to organize your data. The CKRecord class defines the interfaces for managing the contents of records. CloudKit also relies heavily on the use of Operation objects to manage the asynchronous transfer of data to and from the server.
Before using CloudKit, make sure it’s the most suitable option for your app. For more information, see deciding-whether-cloudkit-is-right-for-your-app.
> Note:
 The classes of the CloudKit framework aren’t for subclassing. Use these classes as-is to save, retrieve, and manipulate data in iCloud. In addition, many of the protocols of this framework aren’t for adoption by classes outside of CloudKit and UIKit. Each protocol reference document includes information about whether you can adopt the protocol in your own classes.
