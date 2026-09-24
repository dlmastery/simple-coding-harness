"""Compare index blobs with raw evidence bytes before/after line-ending preservation."""
import argparse
import csv
import hashlib
from pathlib import Path
import subprocess

repo=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser()
parser.add_argument("--output",required=True,type=Path)
parser.add_argument("--expect-identical",action="store_true")
args=parser.parse_args()
listing=subprocess.run(["git","ls-files","-s","-z","--","rsi/evidence"],cwd=repo,capture_output=True,check=True).stdout
rows=[];count=0
for raw in listing.split(b"\0"):
    if not raw:continue
    header,name=raw.split(b"\t",1);path=name.decode("utf-8")
    _,index_hash,stage=header.decode().split()
    if stage!="0":raise SystemExit("Unmerged evidence: "+path)
    data=(repo/path).read_bytes();count+=1
    raw_blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    if raw_blob==index_hash:continue
    indexed=subprocess.run(["git","cat-file","blob",index_hash],cwd=repo,capture_output=True,check=True).stdout
    equivalent=data.replace(b"\r\n",b"\n")==indexed.replace(b"\r\n",b"\n")
    rows.append([path,index_hash,raw_blob,hashlib.sha256(data).hexdigest(),equivalent])
    if not equivalent:raise SystemExit("Non-line-ending difference requires investigation: "+path)
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open("w",encoding="utf-8",newline="") as stream:
    writer=csv.writer(stream,lineterminator="\n")
    writer.writerow(["path","index_blob_sha1","raw_blob_sha1","raw_sha256","only_line_endings_differ"])
    writer.writerows(rows)
print(f"Inspected {count} indexed evidence files; {len(rows)} raw/index differences; all differences limited to line endings.")
if args.expect_identical and rows:raise SystemExit("Raw evidence differs from the index")
