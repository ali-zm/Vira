from treeNode import TreeNode
class ProductVariable(TreeNode):
    
    def __init__(self, _title, _id, _porperty):
        self.title = _title
        self.id = _id
        self.property = _porperty
        self.products = []

    def add_product(self,newProd):
        self.products.append(newProd)