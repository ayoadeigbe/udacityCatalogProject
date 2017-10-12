import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()



# create table
class CatalogDB(Base):
	__tablename__ = 'catalog_table'
	category_name = Column(String(100), nullable = False, primary_key = True)
	category_url = Column(String(250))	
	item_id = Column(Integer, nullable = False)
	
	
class ItemsDB(Base):
	__tablename__ = 'items_table'
	category_name = Column(String(100), ForeignKey('catalog_table.category_name'))
	category_item = Column(String(100), nullable = False)
	item_description = Column(String(250), nullable = False)
	item_creator = Column(String(250), nullable = False)
	item_id = Column(Integer, primary_key = True)
	catalog_table = relationship(CatalogDB)


	#Return json object in serializeable format
	@property
	def serialize(self):
		return {
			'category_name' : self.category_name,
			'category_item' : self.category_item,
			'item_description' : self.item_description,
			'item_creator' : self.item_creator,
			'item_id' : self.item_id,
		}
		
		
engine = create_engine(
'sqlite:///foodcatalog.db')
Base.metadata.create_all(engine)