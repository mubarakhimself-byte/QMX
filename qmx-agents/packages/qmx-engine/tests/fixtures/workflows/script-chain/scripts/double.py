import json
import sys

numbers = json.load(sys.stdin)["in"]
print(json.dumps([2 * n for n in numbers]))
