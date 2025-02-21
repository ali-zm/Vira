import mysql.connector
import re
import json
import requests
import phpserialize
import gzip
from phpserialize import unserialize
from treeNode import TreeNode
from labelTreeNode import LabelTreeNode
from product import Product
from productVariable import ProductVariable
from woocommerce import API




def fetch_data(DBaddr):
    connection = mysql.connector.connect(host="developer.merpco.com",
        database="developermerpco_merp_2",
        user=DBusername,
        password=DBpassword)
    try:
        
        sql_select_Query = "select * from " + DBaddr
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        records = cursor.fetchall()
        num_fields = len(cursor.description)
        field_names = [i[0] for i in cursor.description]
        return records, field_names
    except mysql.connector.Error as e:
        print("Data Fetching Error :", e)
    finally:
        if connection.is_connected():
            connection.close()
            cursor.close()
            print("connection closed")

def decode_bytes(d):
    if isinstance(d, dict):
        return {key.decode('utf-8'): decode_bytes(value) for key, value in d.items()}
    elif isinstance(d, list):
        return [decode_bytes(item) for item in d]
    elif isinstance(d, bytes):
        return d.decode('utf-8')
    else:
        return d


def file_uploaded_info(unique_id, file_type):

    params = {
        'file_uploaded_info': '1',
        'unique_id': unique_id,
        'type': file_type,
    }

    fake = False

    if fake:
        result = {'alert': 'success', 'data': {'url': '', 'name': '', 'unique_code': unique_id}}
        if isinstance(unique_id, list):
            temp = {}
            for item in unique_id:
                temp[item] = {'url': '', 'name': '', 'unique_code': item}
            result['data'] = temp
    else:
        url = 'https://expo.merpco.com/file_upload_receiver/file_upload_curl.php'
        response = requests.post(url, data=params)

        if response.status_code == 200:
            PHPphrase = (gzip.decompress(response.content))
            unserialized_data = phpserialize.loads(PHPphrase)
            result = decode_bytes(unserialized_data)

        else:
            result = None

    return result


def assign_image_url():
    for key, value in IDandNodelabelDB.items():
        if value.image != "":
            try:
                url = file_uploaded_info(value.image, "get_info")["data"]["url"]
                value.image = url
            except:
                print("image not found")
                value.image = ""
    for key, value in IDandProductDB.items():
        if value.image != "":
            try:
                url = file_uploaded_info(value.image, "get_info")["data"]["url"]
                value.image = url
            except:
                print("image not found")
                value.image = ""


def add_parent_to_node(sample, headings, curDict):
    curDict[sample[headings.index("id")]].add_parent(curDict[sample[headings.index("parent_id")]])
        


def create_tree_of_property(data, headings):
    IDandTreenode = {}
    # create nodes
    for sample in data:
        newSample = TreeNode(sample[headings.index("title")],sample[headings.index("id")])
        # add parent
        IDandTreenode[sample[headings.index("id")]] = newSample 
        if sample[headings.index("parent_id")] != 0 :
            add_parent_to_node(sample, headings, IDandTreenode)
    return IDandTreenode

def create_tree_of_label(data, headings,):
    IDandTreenode = {}
    # create nodes
    for sample in data:
        newSample = LabelTreeNode(sample[headings.index("title")], sample[headings.index("id")], sample[headings.index("label_id")], sample[headings.index("image")])
        IDandTreenode[sample[headings.index("id")]] = newSample
        
        if sample[headings.index("parent_id")] == 0 :
            IDandTreenode[sample[headings.index("id")]].IsRoot = True
        else: 
            add_parent_to_node(sample, headings, IDandTreenode)
    return IDandTreenode
 

def create_nodes_of_product(data,headings):
    IDandProductDB = {}
    for sample in data:
        newSample = Product(sample[headings.index("site_title")], sample[headings.index("id")], sample[headings.index("type")], 
                                sample[headings.index("codding")], sample[headings.index("warehouse_id")], sample[headings.index("main_picture")],
                                    sample[headings.index("customer_id")], sample[headings.index("main_unit")])
        IDandProductDB[sample[headings.index("id")]] = newSample
    return IDandProductDB

def assign_price_to_products(IDandProductDB, pricesData, priceHeadings):
    for sample in pricesData:
        try:
            curProduct = IDandProductDB[sample[priceHeadings.index("product_id")]]
            curProduct.price = sample[priceHeadings.index("last_sale")]
        except:
            print(f'product{sample[priceHeadings.index("product_id")]} not found to assign price')
            continue



def unserialize_and_integerize_php_phrase(PHPphrase):
    unserialized = unserialize(PHPphrase.encode('utf-8'))
    for k, v in unserialized.items():
        if type(v)==dict:
            for j, t in v.items():
                if len(t)!=0:
                    try:
                        v[j]=int(t[0])
                    except:
                        continue
            unserialized[k]=v
        else:
            unserialized[k] = int(v)
    return unserialized

def create_variable_products(data, headings, IDandProductDB):
    IDandVariableProductDB = {}
    productTreeDB = {}
    for sample in data:
        curProduct = IDandProductDB[sample[headings.index("id")]]
        curProperty = sample[headings.index("property")]
        if curProperty != None and curProperty!='':
            curProperty = unserialize_and_integerize_php_phrase(curProperty)
            # create variable product
            if sample[headings.index("slave")] == sample[headings.index("id")]:
                newProductVar = ProductVariable(curProduct.title, str(curProduct.id)+"var", IDandNodePropertyDB[list(curProperty.keys())[0]])
                IDandVariableProductDB[curProduct.id] = newProductVar
                productTreeDB[curProduct.id] = newProductVar
        else:
            productTreeDB[curProduct.id] = curProduct
    return IDandVariableProductDB, productTreeDB    

def add_slaves(sample, headings, IDandProductDB, IDandVariableProductDB):
    curProduct = IDandProductDB[sample[headings.index("id")]]
    curProperty = sample[headings.index("property")]
    if curProperty != None and curProperty!='':
        curProperty = unserialize_and_integerize_php_phrase(curProperty)
        slaveID = sample[headings.index("slave")]
        curProduct.propertyOfVariable = IDandNodePropertyDB[list(curProperty.values())[0]]
        IDandVariableProductDB[slaveID].add_product(curProduct)


                   
def add_relative_products(sample, headings, IDandProductDB):
    curProduct = IDandProductDB[sample[headings.index("id")]]
    curMasterID = sample[headings.index("master")]
    if curMasterID == 0:
        return
    curMaster = IDandProductDB[curMasterID]
    if curMaster==curProduct:
        curMaster.add_related_product(curProduct)
    else:
        curMaster.add_related_product(curProduct)
        curProduct.add_related_product(curMaster)

def add_label(curProduct, curLabel):
    if curLabel.type==TAG_ID:
        curProduct.add_tag(curLabel)
    elif curLabel.type==BRAND_ID:
        curProduct.brand = curLabel
    curProduct.add_label(curLabel)

def add_property(curProduct, propertiesID):
    for parentPropertyID, childPropertyID in propertiesID.items():
        if type(childPropertyID)==int:
            if childPropertyID in IDandNodePropertyDB:
                curProduct.add_applied_properties(IDandNodePropertyDB[childPropertyID])
        curProduct.add_possible_properties(IDandNodePropertyDB[parentPropertyID])
        

def add_labels_and_property(sample, headings, IDandProductDB):
    curProduct = IDandProductDB[sample[headings.index("id")]]
    curLabels = unserialize_and_integerize_php_phrase(sample[headings.index("label")])
    for labelID, propertiesID in curLabels.items():
        curLabel = IDandNodelabelDB[labelID]
        add_label(curProduct, curLabel)
        if propertiesID.items() != None:
            add_property(curProduct, propertiesID)
    try: 
        curProduct.category = IDandNodelabelDB[sample[headings.index("group_id")]]
    except:
        print(f'label{sample[headings.index("group_id")]} not found to be assigned to a product')
        return
        



def complete_product_info(data, headings, IDandProductDB, IDandVariableProductDB):
    for sample in data:
        add_slaves(sample, headings, IDandProductDB, IDandVariableProductDB)
        add_relative_products(sample, headings, IDandProductDB)
        add_labels_and_property(sample, headings, IDandProductDB)


def create_tree_of_product(productData, productHeadings, pricesData, priceHeadings):
    IDandProductDB = create_nodes_of_product(productData, productHeadings)
    assign_price_to_products(IDandProductDB, pricesData, priceHeadings)
    IDandVariableProductDB, productTreeDB = create_variable_products(productData, productHeadings, IDandProductDB)
    complete_product_info(productData, productHeadings, IDandProductDB, IDandVariableProductDB)
    return IDandProductDB, IDandVariableProductDB, productTreeDB










def create_category_woo(obj, idCategoryDBintoWOO):
    if obj.IsRoot:
        parentID = 0
    else:
        parentID = idCategoryDBintoWOO[obj.parent.id]
    newCategoryData = {
        "name":obj.title, 
        "parent":parentID
    }
    if obj.image != "":
        newCategoryData["images"]=[{"src":obj.image}]
    response = wcapi.post("products/categories", newCategoryData).json()
    try:
        idCategoryDBintoWOO[obj.id] = response['id']
    except:
        print(response, parentID)


def create_tag_woo(obj, idTagDBintoWOO):
    newTagData = {
        "name":obj.title
    }
    response = wcapi.post("products/tags", newTagData).json()
    try:
        idTagDBintoWOO[obj.id] = response["id"]
    except:
        print(response) 


def create_woocommerce_categories_tags(IDandNodelabelDB):
    idCategoryDBintoWOO = {}
    idTagDBintoWOO = {}
    for _,  obj in IDandNodelabelDB.items():
        if obj.type == CATEGORY_ID:
            create_category_woo(obj, idCategoryDBintoWOO)
        elif obj.type == TAG_ID or obj.type == BRAND_ID:
            create_tag_woo(obj, idTagDBintoWOO)
    return idCategoryDBintoWOO, idTagDBintoWOO
            
                
def create_attribute_woo(obj, idPropertyDBintoWOO):
    newAttributeData = {
                "name":obj.title, 
                "type":"select",
                "order_by": "menu_order",
                "has_archives": True
            }
    response = wcapi.post("products/attributes", newAttributeData).json()
    try:
        idPropertyDBintoWOO[obj.id] = response["id"]
    except:
        print(response)


def add_term_woo(obj, idPropertyDBintoWOO):
    newTermData = {
        "name":obj.title
    }
    parentIDwoo = idPropertyDBintoWOO[obj.parent.id]
    response = wcapi.post(f"products/attributes/{parentIDwoo}/terms", newTermData).json()
    try:
        idPropertyDBintoWOO[obj.id] = response["id"]
    except:
        print(response)


def create_woocommerce_attributes_and_terms(IDandNodePropertyDB):
    idPropertyDBintoWOO = {}  
    for _, obj in IDandNodePropertyDB.items():
        if obj.parent == None:
            create_attribute_woo(obj, idPropertyDBintoWOO)
        else:
            add_term_woo(obj, idPropertyDBintoWOO)
    return idPropertyDBintoWOO


def create_simple_product_woo(obj, idProductDBandWOO):
    properties = [{"id":idPropertyDBintoWOO[i.parent.id], "options":[i.title]}for i in obj.appliedProperties]
    category = [{"id":idCategoryDBintoWOO[obj.category.id]}]
    tags = [{"id":idTagDBintoWOO[i.title]}for i in obj.tags]
    newProductData = { 
            "name":obj.title,
            "type":"simple",
            "regular_price": obj.price,
            "description":"", 
            "short_description":"",
            "attributes":properties,
            "categories":category,
            "tags": tags,
            "meta_data": [
                {
                    "key": "id-db",
                    "value": obj.id
                }
            ]
    }
    if obj.image != "":
        newProductData["images"]=[{"src":obj.image}]
    response = wcapi.post("products", newProductData).json()
    try:
        idProductDBandWOO[obj.id] = response["id"]
    except:
        print(response)



def create_variations_woo(obj, idProductDBandWOO):
    idVarProperty = idPropertyDBintoWOO[obj.property.id]
    for variationProduct in obj.products:
        newVariationData = {
            "regular_price": variationProduct.price,
            "meta_data": [
                {
                    "key": "id-db",
                    "value": variationProduct.id
                }
            ],
            "attributes": [
                {
                    "id": idVarProperty,
                    "option": variationProduct.propertyOfVariable.title
                }
            ]
        }
        if variationProduct.image != "":
            newVariationData["image"]={"src":variationProduct.image}
        curVariableId = idProductDBandWOO[obj.id]
        response = wcapi.post(f"products/{curVariableId}/variations", newVariationData).json()
        try:
            idProductDBandWOO[variationProduct.id] = response["id"]
        except:
            print(response)


def create_variable_product_woo(obj, idProductDBandWOO):
    idVarProperty = idPropertyDBintoWOO[obj.property.id]
    options = [i.propertyOfVariable.title for i in obj.products]
    category = [{"id":idCategoryDBintoWOO[obj.products[0].category.id]}]
    newProductVariableData = {
            "name":obj.title,
            "type":"variable",
            "description":"", 
            "short_description":"",
            "categories":category,
            "attributes" : [
                {
                    "id": idVarProperty,
                    "position": 0,
                    "visible": True,
                    "variation": True,
                    "options": options
                }
            ]
    }
    for variation in obj.products:
        if variation.image != "":
            if "images" in newProductVariableData:
                newProductVariableData["images"].append({"src":variation.image})
            else:
                newProductVariableData["images"]=[{"src":variation.image}]
    response = wcapi.post("products", newProductVariableData).json()
    idProductDBandWOO[obj.id] = response["id"]
    create_variations_woo(obj, idProductDBandWOO)

def create_woocommerce_products(productTreeDB):
    idProductDBandWOO = {}
    for _, obj in productTreeDB.items():
        try:
            if type(obj)==ProductVariable:
                create_variable_product_woo(obj, idProductDBandWOO)
            elif type(obj)==Product:
                create_simple_product_woo(obj, idProductDBandWOO)
        except:
            continue
            









# # main
TAG_ID = 11
BRAND_ID = 13
CATEGORY_ID = 1

labelsDBaddr = "co_acc_goodsGroup"
propertyDBaddr = "co_acc_good_property_new"
productDBaddr = "co_acc_goods_services"
assignlabelToProductDBaddr = "co_product_assign_property"
priceDBaddr = "co_acc_good_price"

print("Enter DB Username: ")
DBusername = input()
print("Enter DB Password: ")
DBpassword = input()
print("Enter Your WooCommerce Store URL: ")
wooComStoreUrl = input()
print("Enter Your WooCommerce Consumer key: ")
wooComStoreConsumerKey = input()
print("Enter Your WooCommerce Consumer Secret: ")
wooComStoreConsumerSecret = input()

wcapi = API(
  url=wooComStoreUrl,
  consumer_key=wooComStoreConsumerKey,
  consumer_secret=wooComStoreConsumerSecret,
  timeout = 30
)


properties, propertiesheadings = fetch_data(propertyDBaddr)
labels, labelsheadings = fetch_data(labelsDBaddr)
products, productsheadings = fetch_data(productDBaddr)
prices, priceheadings = fetch_data(priceDBaddr)



IDandNodePropertyDB = create_tree_of_property(properties, propertiesheadings)
IDandNodelabelDB = create_tree_of_label(labels, labelsheadings)
IDandProductDB, IDandVariableProductDB, productTreeDB = create_tree_of_product(products, productsheadings, prices, priceheadings)

assign_image_url()

idCategoryDBintoWOO, idTagDBintoWOO = create_woocommerce_categories_tags(IDandNodelabelDB)
idPropertyDBintoWOO = create_woocommerce_attributes_and_terms(IDandNodePropertyDB)
create_woocommerce_products(productTreeDB)
