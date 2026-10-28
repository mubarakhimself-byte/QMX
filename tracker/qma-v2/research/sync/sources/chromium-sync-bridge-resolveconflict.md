<!-- Source: https://chromium.googlesource.com/chromium/src/+/main/components/sync/model/data_type_sync_bridge.h
     Fetched: 2026-10-28. Excerpt (lines 185-199), verbatim. -->

```cpp
  // Extract unique position from specifics, called for non-deletions only.
  // Unique position is supposed to be stored in specifics (and hence, generated
  // before the Put() call) but locally it's stored in sync metadata by the
  // processor. Returns the default proto if the entity does not have / require
  // unique position.
  virtual sync_pb::UniquePosition GetUniquePosition(
      const sync_pb::EntitySpecifics& specifics) const;

  // Resolve a conflict between the client and server versions of data. They are
  // guaranteed not to match (both be deleted or have identical specifics). A
  // default implementation chooses the server data unless it is a deletion.
  virtual ConflictResolution ResolveConflict(
      const std::string& storage_key,
      const EntityData& remote_data) const;

```
