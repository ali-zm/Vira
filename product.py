class Product():
    def __init__(self, _title, _id, _type, _codding, _warehouseId, _mainPicture, _customerID, _mainUnit):
        self.title = _title
        self.id = _id
        self.relatedProducts = []
        self.propertyOfVariable = None
        self.type = _type
        self.codding = _codding
        self.warehouseID = _warehouseId
        self.image = _mainPicture
        self.customerID = _customerID
        self.mainUnit = _mainUnit
        self.category = None
        self.possibleProperties=[]
        self.appliedProperties=[]
        self.labels = []
        self.tags = []
        self.brand = None
        self.price = "0"

    def add_related_product(self, newRelatedProduct):
        self.relatedProducts.append(newRelatedProduct)

    def add_possible_properties(self,property):
        self.possibleProperties.append(property)
    
    def add_applied_properties(self,property):
        self.appliedProperties.append(property)

    def add_label(self, label):
        self.labels.append(label)

    def add_tag(self, tag):
        self.tags.append(tag)

    