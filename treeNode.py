class TreeNode:
    def __init__(self, _title, _id):
        self.title = _title
        self.id = _id
        self.children = []
        self.parent = None
        self.IsRoot = False
        
    def add_parent(self, parent):
        self.parent = parent
        parent.children.append(self)