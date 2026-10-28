<!-- Source: https://developer.apple.com/documentation/foundation/nsubiquitouskeyvaluestore
     Fetched: 2026-10-28 via the page's documentation JSON (https://developer.apple.com/tutorials/data/documentation/foundation/nsubiquitouskeyvaluestore.json); text extracted. -->

# NSUbiquitousKeyValueStore
An iCloud-based container of key-value pairs you share among instances of your app running on a person’s devices.

## Overview
Use the shared `NSUbiquitousKeyValueStore` object to store settings, configuration information, and app-specific data in a person’s iCloud account and share it among instances of your app running on all of the person’s devices. The object stores a dictionary of key-value pairs that you provide, and propagates that data to devices with the same Apple account. Sharing data among different devices gives you a way to coordinate your app’s behavior on those devices. For example, a textbook app might save the current page number on someone’s iPhone so that the person can continue reading from the same place on their other devices.
> Important:
Don’t store personal or sensitive information in the key-value store. The system stores the information on disk in an unencrypted format. Store personal or sensitive information in the person’s Keychain instead.
Each app has a single iCloud key-value store object, which you retrieve from the default class property. Use this same object throughout your app to read and write values. Don’t subclass `NSUbiquitousKeyValueStore`.
> Note:
To use this object, you must distribute your app through the App Store or Mac App Store, and you must request the com.apple.developer.ubiquity-kvstore-identifier in your Xcode project.
The keys in the iCloud key-value store identify the item and its purpose in your app, and the value is a data object you use to implement the corresponding behavior in your app. Values must be property list types such as Int64, Float, Double, Bool, String, NSNumber, Date, Array, or Dictionary. To include other types of objects in the key-value store, archive them to a Data object first and store that object instead. Prefer simple types over custom objects whenever possible.
When you write a new value, the iCloud key-value store saves it in memory initially and writes it to disk asynchronously later. If the device doesn’t have an active Apple account, the changes remain only on the current device. When the person signs into their account, the system forwards any changes to the iCloud server and reconciles the values there with the local ones. As you make more changes, the system keeps the local and server-based copies of the data synchronized, updating each one at appropriate times.
When a value changes on one device, iCloud forwards that change to the person’s other devices. If your app is running on one of those other devices, the system posts didChangeExternallyNotification to report the change. Register for that notification to keep all instances of your app in sync.
When designing the keys and values you intend to save for your app, consider the following size limitations:
- 
Your app can have no more than 1024 keys in the iCloud key-value store.
- 
The total amount of available storage space for all values is 1 megabyte.
- 
The maximum size for a single value is 1 megabyte. Therefore, if you associate 1 megabyte of data with a single key, you can’t write other keys to the store.
- 
The maximum length for each key string is 128 characters using the UTF-16 encoding. Key strings don’t count against the 1 megabyte quota for values.
If you exceed any of the prescribed limits during a write operation, the operation fails and the system doesn’t add the keys or values to the store. If a key string exceeds the maximum length, the system raises an exception. If a write operation would exceed your app’s quota, the system posts didChangeExternallyNotification notification with the change reason set to NSUbiquitousKeyValueStoreQuotaViolationChange.
