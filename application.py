from application_db import Base, CatalogDB, ItemsDB
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine('sqlite:///foodcatalog.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind = engine)
session = DBSession()

#Seed content for category listed on the Mainpage
myCatalogDB = CatalogDB(category_name = "WINE", category_url = "http://img.mshanken.com/d/wso/slider/WAIT_1600.jpg", item_id =1)
session.add(myCatalogDB)
session.commit()
myCatalogDB = CatalogDB(category_name = "CAKE", category_url = "http://food.fnr.sndimg.com/content/dam/images/food/fullset/2014/2/19/1/WU0701H_Molten-Chocolate-Cakes_s4x3.jpg.rend.hgtvcom.616.462.jpeg", item_id =2)
session.add(myCatalogDB)
session.commit()
myCatalogDB = CatalogDB(category_name = "FOOD SAUCE", category_url = "https://bit.ua/wp-content/uploads/2017/03/1-8.jpg", item_id =3)
session.add(myCatalogDB)
session.commit()

#Seed content for each category
myItemsDB = ItemsDB(category_name = "WINE", category_item = "Chardonnay", item_id =1, item_description = "Chardonnay was the most popular white grape through the 1990s. It can be made sparkling or still.", item_creator = "admin@admin.com" )
session.add(myItemsDB)
session.commit()

myItemsDB = ItemsDB(category_name = "CAKE", category_item = "Batik Cake", item_id =2, item_description= "A non-baked cake dessert made by mixing broken Marie biscuits, combined with a chocolate sauce or runny custard", item_creator = "admin@admin.com" )
session.add(myItemsDB)
session.commit()

myItemsDB = ItemsDB(category_name = "FOOD SAUCE", category_item = "Egusi Soup", item_id =3, item_description= "Egusi soup is a culinary soup prepared with egusi seeds as a primary ingredient. Egusi soup is also consumed in West Africa, sometimes with chicken", item_creator = "admin@admin.com" )
session.add(myItemsDB)
session.commit()

