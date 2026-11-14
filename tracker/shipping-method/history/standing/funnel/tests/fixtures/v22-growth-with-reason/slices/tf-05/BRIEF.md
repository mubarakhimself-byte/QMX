# tf-05: heartbeat 30s

Serves: S1 in `SCOPE.md`. Stop point: B. Lane: L5. Depends on: none.
Chain: S1.a; A1; E1

## 3. Facts

```fact F1
$ git grep -c "heartbeat_s" -- qmn/src
qmn/src/qmn/config.py:1
```

## 7a. Edge-case scenarios

- E1 heartbeat edge: value holds (test: test_heartbeat_value)

## 8. Safety

```fact SAFETY exit=1
$ git grep -n "keyring" -- qmn/src/qmn/config.py
```

## 9. Done when

- [ ] value is 30. Operations: the existing heartbeat watches it (test: test_heartbeat_value).

## 10. Size guide

S.

## 11. Merge request

- Title: tf-05: heartbeat 30s
- In plain words: the node checks it is alive every 30 seconds.
- TRACE: tf-05 -> S1.a -> S1
- Door: two-way, because one config value. Blast radius: the heartbeat only, proved safe by fact SAFETY.
- DOC: none
- OPEN known at planning: none
