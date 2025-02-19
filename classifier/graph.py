import sqlite3
import json

DB_PATH = "../classified.db"

def fetch_tree_data():
    """ Fetch parent-child relationships from SQLite and construct a tree structure. """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT Parent, Child FROM filesteps")
    rows = cursor.fetchall()
    conn.close()

    # Step 1: Create adjacency list
    tree = {}
    for parent, child in rows:
        if parent not in tree:
            tree[parent] = []
        tree[parent].append(child)

    # Step 2: Convert adjacency list to hierarchical JSON
    def build_tree(node):
        return {"name": node, "children": [build_tree(child) for child in tree.get(node, [])]}

    # Step 3: Find root node(s) (nodes that are never a child)
    all_nodes = set(tree.keys()) | {child for children in tree.values() for child in children}
    root_nodes = [node for node in tree.keys() if node not in {child for children in tree.values() for child in children}]
    
    # Create JSON structure with a single root node
    hierarchy = {"name": "Root", "children": [build_tree(root) for root in root_nodes]}

    # Step 4: Save to JSON file
    with open("file_structure.json", "w") as f:
        json.dump(hierarchy, f, indent=2)

    print("Exported to file_structure.json")

# Run the export function
fetch_tree_data()
