import re

with open("random_egograph.gml") as f:
    text = f.read()

edges = re.findall(r'edge\s*\[\s*source\s+(\d+)\s+target\s+(\d+)', text)

with open("egograph_edges.txt","w") as f:
    for s,t in edges:
        f.write(f"{s} {t}\n")