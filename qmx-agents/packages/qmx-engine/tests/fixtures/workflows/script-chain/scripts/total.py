import json
import sys

print(json.dumps({"total": sum(json.load(sys.stdin)["in"])}))
