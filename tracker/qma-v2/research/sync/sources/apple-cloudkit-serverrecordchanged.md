<!-- Source: https://developer.apple.com/documentation/cloudkit/ckerror/code/serverrecordchanged
     Fetched: 2026-10-28 via the page's documentation JSON (https://developer.apple.com/tutorials/data/documentation/cloudkit/ckerror/code/serverrecordchanged.json); text extracted. -->

# CKError.Code.serverRecordChanged
An error that occurs when CloudKit rejects a record because the server’s version is different.

## Discussion
This error indicates that the server’s version of the record is newer than the local version the client’s trying to save. Your app needs to handle this error, resolve any conflicts in the record, and attempt another save of the record, if necessary.
CloudKit provides your app with three copies of the record in this error’s `userInfo` dictionary to assist with comparing and merging the changes:
- 
CKRecordChangedErrorClientRecordKey: The local record that the client’s trying to save.
- 
CKRecordChangedErrorServerRecordKey: The record that exists on the server.
- 
CKRecordChangedErrorAncestorRecordKey: The original version of the record.
When a conflict occurs, your app needs to merge all changes into the record for the CKRecordChangedErrorServerRecordKey key and attempt a new save using that record. Merging into either of the other two copies of the record results in another conflict error because those records have the old record change tag.
