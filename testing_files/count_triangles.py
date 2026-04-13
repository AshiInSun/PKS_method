import os
from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

def count_triangles_in_graph(file_path):
    graph = Graph(directed=False)
    graph.read_ssv(file_path)
    mc = MarkovChain(graph)
    mc.count_triangles()
    triangles = len(mc.triangles2edges)
    return triangles

def main():
    out_dir = '../out'
    triangle_counts = {}


    for filename in os.listdir(out_dir):
        if filename.startswith('test'):
            file_path = os.path.join(out_dir, filename)
            try:
                count = count_triangles_in_graph(file_path)
                triangle_counts[filename] = count
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Check if all have the same number
    counts = list(triangle_counts.values())
    if len(set(counts)) == 1:
        print(f"All graphs have the same number of triangles: {counts[0]}")
    else:
        print("Graphs have different numbers of triangles:")
        for filename, count in triangle_counts.items():
            print(f"{filename}: {count}")

    # Print summary
    print(f"\nProcessed {len(triangle_counts)} files.")
    print(f"Unique triangle counts: {set(counts)}")

if __name__ == "__main__":
    main()
