# QMB Windows diagnostic assertion review (draft)

The refusal's reason already contains the diagnostic filename. Converting the
whole context mapping to repr escapes Windows backslashes. Assert against the
reason field's actual text, retaining the filename requirement. Evidence:
structural-reviewed/pytest.txt: 74 passed, four preexisting POSIX chmod skips.
Self-review: assertion only; CLI refusal behavior is unchanged.
