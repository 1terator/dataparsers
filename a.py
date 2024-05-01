class TreeRoot:
    def __init__(self, name):
        self.name = name
        self.children = []


def insert_path(root: TreeRoot, path_parts):
    current_node = root
    for part in path_parts:
        found = False
        for child in current_node.children:
            if child.name == part:
                current_node = child
                found = True
                break
        if not found:
            new_node = TreeRoot(part)
            current_node.children.append(new_node)
            current_node = new_node


def build_tree(paths) -> TreeRoot:
    root = TreeRoot(paths[0].split("/")[0])
    for path in paths:
        path_parts = path.split("/")
        insert_path(root, path_parts[1:])
    return root


def print_tree(root: TreeRoot, depth=0):
    if root:
        indent = "  " * depth
        print(indent + root.name)
        for child in sorted(root.children, key=lambda x: x.name):
            print_tree(child, depth + 1)


n = int(input().strip())
paths = [input().strip() for _ in range(n)]

root = build_tree(paths)
print_tree(root)
