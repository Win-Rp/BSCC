import re
import sys

FILES = [
    r"d:/Office/Rp/Dev/BSCC/miniprogram/pages/progress/index.wxml",
    r"d:/Office/Rp/Dev/BSCC/miniprogram/pages/upload/index.wxml",
]

TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w-]*)(\"[^\"]*\"|'[^']*'|[^>\"'/])*>")

failed = False
for path in FILES:
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    stack = []
    ok = True
    for m in TAG_RE.finditer(text):
        closing, tag, rest = m.group(1), m.group(2), m.group(3)
        if (rest or "").rstrip().endswith("/"):
            continue
        if closing:
            if not stack or stack[-1] != tag:
                print("MISMATCH in", path, "tag", tag, "tail", stack[-3:])
                ok = False
                break
            stack.pop()
        else:
            stack.append(tag)
    if ok and stack:
        print("UNCLOSED in", path, stack)
        ok = False
    if ok:
        print("WXML OK:", path.split("/")[-3])
    failed = failed or not ok

sys.exit(1 if failed else 0)
