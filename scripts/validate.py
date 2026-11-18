#!/usr/bin/env python3
"""Validate every n8n workflow export in workflows/."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_TYPES = {
    "n8n-nodes-base.webhook", "n8n-nodes-base.respondToWebhook", "n8n-nodes-base.gmailTrigger",
    "n8n-nodes-base.gmail", "n8n-nodes-base.telegramTrigger", "n8n-nodes-base.telegram",
    "n8n-nodes-base.googleSheets", "n8n-nodes-base.googleSheetsTrigger", "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.if", "n8n-nodes-base.switch", "n8n-nodes-base.set", "n8n-nodes-base.code",
    "n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.rssFeedRead", "n8n-nodes-base.merge",
    "n8n-nodes-base.stickyNote", "n8n-nodes-base.googleCalendar",
    "@n8n/n8n-nodes-langchain.agent", "@n8n/n8n-nodes-langchain.lmChatOpenAi",
    "@n8n/n8n-nodes-langchain.chainLlm", "@n8n/n8n-nodes-langchain.memoryBufferWindow",
    "@n8n/n8n-nodes-langchain.outputParserStructured",
}
CONN_TYPES = {"main", "ai_languageModel", "ai_memory", "ai_outputParser", "ai_tool", "ai_embedding", "ai_vectorStore"}
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}", r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b", r"AIza[0-9A-Za-z_-]{30,}",
    r"gh[pousr]_[A-Za-z0-9]{30,}", r"xox[abprs]-[A-Za-z0-9-]{10,}", r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"(?i)(api[_-]?key|secret|token|password)\"\s*:\s*\"[^\"]{12,}\"",
    r"AKIA[0-9A-Z]{16}",
]


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def check(path):
    errs = []
    try:
        wf = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa
        return [f"invalid JSON: {e}"]
    for key in ("name", "nodes", "connections", "settings"):
        if key not in wf:
            errs.append(f"missing top-level '{key}'")
    nodes = wf.get("nodes", [])
    names, ids = set(), set()
    for n in nodes:
        nm = n.get("name", "<unnamed>")
        for key in ("id", "name", "type", "typeVersion", "position", "parameters"):
            if key not in n:
                errs.append(f"node '{nm}' missing '{key}'")
        if nm in names:
            errs.append(f"duplicate node name '{nm}'")
        names.add(nm)
        if n.get("id") in ids:
            errs.append(f"duplicate node id '{n.get('id')}'")
        ids.add(n.get("id"))
        if not isinstance(n.get("typeVersion"), (int, float)):
            errs.append(f"node '{nm}' typeVersion must be a number")
        pos = n.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(x, (int, float)) for x in pos)):
            errs.append(f"node '{nm}' position must be [x, y]")
        if n.get("type") not in ALLOWED_TYPES:
            errs.append(f"node '{nm}' has unknown type '{n.get('type')}'")
        for cred in (n.get("credentials") or {}).values():
            if not isinstance(cred, dict) or not cred.get("name"):
                errs.append(f"node '{nm}' credential must be referenced by name")
    for src, kinds in wf.get("connections", {}).items():
        if src not in names:
            errs.append(f"connection source '{src}' is not a node")
        for kind, outs in kinds.items():
            if kind not in CONN_TYPES:
                errs.append(f"connection from '{src}' has unknown type '{kind}'")
            for out in outs:
                for tgt in out:
                    if tgt.get("node") not in names:
                        errs.append(f"connection '{src}' -> '{tgt.get('node')}' targets a missing node")
                    if not isinstance(tgt.get("index"), int):
                        errs.append(f"connection '{src}' -> '{tgt.get('node')}' needs integer index")
    if not any(t.endswith(("Trigger", "webhook")) or t.endswith("Trigger") for t in (n.get("type", "") for n in nodes)):
        errs.append("workflow has no trigger node")
    blob = "\n".join(strings(wf)) + "\n" + path.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        m = re.search(pat, blob)
        if m:
            errs.append(f"secret-looking value matches /{pat}/: {m.group(0)[:12]}...")
    return errs


def main():
    files = sorted((ROOT / "workflows").glob("*.json"))
    if not files:
        print("no workflows found")
        return 1
    bad = 0
    for f in files:
        errs = check(f)
        print(("FAIL " if errs else "ok   ") + f.name)
        for e in errs:
            print("     - " + e)
        bad += bool(errs)
    print(f"\n{len(files) - bad}/{len(files)} workflows valid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
