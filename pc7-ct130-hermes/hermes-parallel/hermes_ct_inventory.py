#!/usr/bin/env python3
"""Read-only parallel inventory of available LXC guests."""
import concurrent.futures, json, subprocess, sys
NODES=("pc6","pc7","pc8","pc9")
def one(node):
    try:
        p=subprocess.run(["ssh",node,"pct list"],capture_output=True,text=True,timeout=30)
        if p.returncode: return {"node":node,"error":p.stderr.strip()}
        rows=[]
        for line in p.stdout.splitlines()[1:]:
            x=line.split(None,5)
            if len(x)>=4 and x[0].isdigit(): rows.append({"vmid":int(x[0]),"status":x[1],"lock":x[2],"name":x[3],"node":node})
        return {"node":node,"guests":rows}
    except Exception as e: return {"node":node,"error":str(e)}
def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(NODES)) as ex: out=list(ex.map(one,NODES))
    out=sorted(out,key=lambda x:x["node"])
    guests=sorted((g for x in out for g in x.get("guests",[])),key=lambda g:(g["vmid"],g["node"]))
    result={"nodes":out,"guests":guests}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    return 0 if all("error" not in x for x in out) else 1
if __name__=="__main__": sys.exit(main())
