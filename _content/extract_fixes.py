#!/usr/bin/env python3
"""Pull the {area: [fix,...]} map out of a completed QA workflow's output file."""
import json
import sys

raw = open(sys.argv[1]).read()
obj, _ = json.JSONDecoder().raw_decode(raw[raw.index('{'):])
areas = (obj.get("result") or obj).get("areas") or obj.get("areas")
print(json.dumps({a["area"]: a["confirmed"] for a in areas}, ensure_ascii=False, indent=1))
