import os, json, urllib.request

base = os.environ["IR_BASE"].rstrip("/")
key = os.environ["IR_KEY"]
req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + key})
data = json.load(urllib.request.urlopen(req, timeout=30))
ids = sorted(m.get("id", "") for m in data.get("data", []))
print("total", len(ids))
for i in ids:
    print(i)
