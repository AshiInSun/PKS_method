import sys
import json
import glob
import os
from igraph import Graph as IGraph
from collections import defaultdict



def load(path):
    with open(path, "r") as f:
        return json.load(f)


