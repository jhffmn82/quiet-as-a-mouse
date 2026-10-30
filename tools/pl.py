"""PixelLab (api.pixellab.ai/v2) calls for Cozy Pelts: every sprite, animation and effect in the game comes from here.

The key is the one forge-godot already keeps in .secrets/pixellab-api-key.txt (or PIXELLAB_API_KEY); it is never
printed or copied.

  python tools/pl.py balance
  python tools/pl.py job <name> <endpoint> <body.json>     submit, wait, save every image to art/raw/<name>/

A body may give an image as {"file": "path.png"}; it is sent as base64 with its size filled in where asked.
Each job's receipt sits in art/raw/<name>/job.json, so running the same name again re-downloads instead of paying twice.
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request

API = "https://api.pixellab.ai/v2"
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KEY_FILES = [os.path.join(ROOT, ".secrets", "pixellab-api-key.txt"),
             os.path.join(ROOT, "..", "forge-godot", ".secrets", "pixellab-api-key.txt")]


def key():
    k = os.environ.get("PIXELLAB_API_KEY", "").strip()
    for f in KEY_FILES:
        if k:
            break
        if os.path.exists(f):
            lines = [l.strip() for l in open(f, encoding="utf-8") if l.strip() and not l.strip().startswith("#")]
            k = lines[0] if lines else ""
    if not k:
        sys.exit("No PixelLab API key")
    return k


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, headers={"Authorization": "Bearer " + key(),
                                                                     "Content-Type": "application/json"})
    if body is not None:
        req.data = json.dumps(body).encode()
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:1500]
            if e.code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(15 * (attempt + 1))
                continue
            sys.exit("PixelLab %s %s: HTTP %d %s" % (method, path, e.code, msg))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 3:
                time.sleep(10)
                continue
            raise


def balance():
    b = call("GET", "/balance")
    sub = b.get("subscription") or {}
    print("generations %s of %s" % (sub.get("generations"), sub.get("total")))
    return sub.get("generations") or 0


def inline_files(node):
    """{"file": p} -> base64 image; also fills a sibling "size" when the parent asked for {"size": "auto"}."""
    from PIL import Image
    if isinstance(node, dict):
        if set(node) == {"file"}:
            data = open(os.path.join(ROOT, node["file"]), "rb").read()
            return {"type": "base64", "base64": base64.b64encode(data).decode(), "format": "png"}
        out = {}
        for k, v in node.items():
            out[k] = inline_files(v)
        if out.get("size") == "auto" and isinstance(node.get("image"), dict) and "file" in node["image"]:
            w, h = Image.open(os.path.join(ROOT, node["image"]["file"])).size
            out["size"] = {"width": w, "height": h}
        return out
    if isinstance(node, list):
        return [inline_files(v) for v in node]
    return node


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cozy-pelts)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def images_in(node, found):
    """Every image a response holds, in order: base64 dicts, data URLs, or http links to .png/.gif/.zip/.json."""
    if isinstance(node, dict):
        if isinstance(node.get("base64"), str) and len(node["base64"]) > 100:
            s = node["base64"].split(",", 1)[-1]
            found.append(("png", base64.b64decode(s)))
            return
        for k, v in node.items():
            if k in ("conversation",):
                continue
            images_in(v, found)
    elif isinstance(node, list):
        for v in node:
            images_in(v, found)
    elif isinstance(node, str):
        if node.startswith("data:image"):
            found.append(("png", base64.b64decode(node.split(",", 1)[1])))
        elif node.startswith("http") and node.split("?")[0].rsplit(".", 1)[-1] in ("png", "gif", "json", "zip"):
            found.append((node.split("?")[0].rsplit(".", 1)[-1], node))


def wait(job_id):
    while True:
        j = call("GET", "/background-jobs/%s" % job_id)
        if j.get("status") == "completed":
            return j
        if j.get("status") == "failed":
            sys.exit("job %s failed: %s" % (job_id, json.dumps(j.get("last_response"))[:800]))
        time.sleep(6)


def job(name, endpoint, body_path):
    out = os.path.join(ROOT, "art", "raw", name)
    os.makedirs(out, exist_ok=True)
    receipt = os.path.join(out, "job.json")
    log = json.load(open(receipt)) if os.path.exists(receipt) else {}
    if "response" not in log:
        body = inline_files(json.load(open(os.path.join(ROOT, body_path))))
        r = call("POST", endpoint, body)
        log = {"endpoint": endpoint, "body": body_path, "response": r}
        json.dump(log, open(receipt, "w"), indent=1)
    r = log["response"]
    result = r
    jid = r.get("background_job_id") or (r.get("background_job_ids") or [None])[0]
    if jid:
        j = wait(jid)
        log["usage"] = j.get("usage")
        result = j.get("last_response") or j
        json.dump(log, open(receipt, "w"), indent=1)
    found = []
    images_in(result, found)
    n = 0
    for ext, data in found:
        if isinstance(data, str):
            data = fetch(data)
        path = os.path.join(out, "%02d.%s" % (n, ext))
        open(path, "wb").write(data)
        n += 1
    json.dump({k: v for k, v in (result if isinstance(result, dict) else {}).items()
               if k not in ("images", "image", "conversation")}, open(os.path.join(out, "result.json"), "w"),
              indent=1, default=str)
    print("%s: %d file(s), usage %s" % (name, n, log.get("usage")))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "balance":
        balance()
    elif a[0] == "job" and len(a) == 4:
        job(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)
