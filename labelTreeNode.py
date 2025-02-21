from treeNode import TreeNode

class LabelTreeNode(TreeNode):
    
    def __init__(self, _title, _id, _type, _image):
        TreeNode.__init__(self, _title, _id)
        self.properties = []
        self.products = []
        self.type = _type
        self.image = _image

    def add_properties(self, newProperties):
        for el in newProperties:
            self.properties.append(el)
        
    def add_product(self, product):
        self.products.append(product)
