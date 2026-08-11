#!/usr/bin/env python3
"""Reconstrói um dump SQL plain a partir do pg_dump custom v1.16 (somente leitura).
Gera: schema_pre.sql, data/*.tsv + copy.sql, schema_post.sql
"""
import zlib, os

class Reader:
    def __init__(self, buf):
        self.buf = buf; self.pos = 0
    def byte(self):
        b = self.buf[self.pos]; self.pos += 1; return b
    def take(self, n):
        d = self.buf[self.pos:self.pos+n]; self.pos += n; return d
    def rint(self):
        sign = self.byte()
        val = int.from_bytes(self.take(self.intsize), 'little')
        return -val if sign else val
    def rstr(self):
        n = self.rint()
        return None if n < 0 else self.take(n).decode('utf-8')
    def roffset(self):
        return self.byte(), int.from_bytes(self.take(self.offsize), 'little')

r = Reader(open('BackupNutriJR.copy', 'rb').read())
assert r.take(5) == b'PGDMP'
vmaj, vmin, vrev = r.byte(), r.byte(), r.byte()
r.intsize = r.byte(); r.offsize = r.byte(); fmt = r.byte()
comp = r.byte()
for _ in range(7): r.rint()
r.rstr(); r.rstr(); r.rstr()

ntoc = r.rint()
entries = []
toc = {}
for _ in range(ntoc):
    e = {}
    e['dump_id'] = r.rint(); e['had_dumper'] = r.rint()
    e['tableoid'] = r.rstr(); e['oid'] = r.rstr()
    e['tag'] = r.rstr(); e['desc'] = r.rstr()
    e['section'] = r.rint()
    e['defn'] = r.rstr(); e['drop'] = r.rstr(); e['copy'] = r.rstr()
    e['namespace'] = r.rstr(); e['tablespace'] = r.rstr()
    e['tableam'] = r.rstr(); e['relkind'] = r.rint()
    e['owner'] = r.rstr(); e['withoids'] = r.rstr()
    deps = []
    while True:
        d = r.rstr()
        if d is None: break
        deps.append(d)
    e['deps'] = deps
    r.roffset()
    entries.append(e); toc[e['dump_id']] = e

os.makedirs('rebuild/data', exist_ok=True)

# seções: 2=pre-data, 3=data, 4=post-data (ordem do TOC já é a ordem correta)
SKIP_DESC = {'DATABASE', 'DATABASE PROPERTIES', 'ACL', 'COMMENT', 'SCHEMA'}
with open('rebuild/schema_pre.sql', 'w') as pre, open('rebuild/schema_post.sql', 'w') as post:
    pre.write("SET client_encoding='UTF8'; SET standard_conforming_strings=on;\n")
    for e in entries:
        if e['desc'] in SKIP_DESC or not e['defn']:
            continue
        target = pre if e['section'] <= 2 else post
        if e['section'] == 3:
            continue
        target.write(f"-- {e['desc']}: {e['tag']}\n{e['defn']}\n")

# dados
copies = []
while r.pos < len(r.buf):
    blktype = r.byte()
    if blktype not in (1, 3): break
    dump_id = r.rint()
    d = zlib.decompressobj(); out = bytearray()
    while True:
        n = r.rint()
        if n <= 0: break
        out += d.decompress(r.take(n))
    e = toc[dump_id]
    tag = e['tag']
    open(f'rebuild/data/{tag}.dat', 'wb').write(bytes(out))
    copies.append((tag, e['copy']))

with open('rebuild/copy.sql', 'w') as f:
    for tag, copystmt in copies:
        if copystmt:
            f.write(f"\\echo carregando {tag}\n")
            f.write(copystmt.replace('FROM stdin;', f"FROM '__DATADIR__/{tag}.dat';") + "\n")
print("ok — entradas TOC:", ntoc, "| tabelas com dados:", len(copies))
