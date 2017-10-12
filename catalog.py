from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, make_response
app = Flask(__name__)

import random, string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
import requests

#following import for CRUD functionality
from application_db import Base, CatalogDB, ItemsDB
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Project"


#CONNECT TO DB AND CREATE SESSION
engine = create_engine('sqlite:///foodcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/login')
def UserLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange (32))
	login_session['state'] = state
	return render_template('login.html', STATE = state)

	
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/logout')
@app.route('/gdisconnect')
def gdisconnect():
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(json.dumps('Current User not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %access_token
	h = httplib2.Http()
	result = h.request(url, 'GET') [0]

	if result['status'] =='200':
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


	
	
#API Endpoint JSON GET Request
@app.route('/viewcatalog/<int:item_id>/JSON')
def ViewItemJSON(item_id):
	catalog = session.query(CatalogDB).filter_by(item_id = item_id).one()
	items = session.query(ItemsDB).filter_by(category_name = catalog.category_name).all()
	return jsonify(Catalog_Items=[i.serialize for i in items])	
	
def ViewCatalogJSON(item_id):
	catalog = session.query(CatalogDB).filter_by(item_id = item_id).one()
	items = session.query(ItemsDB).filter_by(category_name = catalog.category_name).all()
	return jsonify(Catalog_Items=[i.serialize for i in items])	

@app.route('/')
@app.route('/index')
def MainPage():
	catalog = session.query(CatalogDB).all()
	if 'username' not in login_session:
		login_status = ""
	else:
		login_status = login_session['email']
	return render_template('index.html', catalog = catalog, login_status = login_status)


@app.route('/viewcatalog/<int:item_id>/')
def ViewCatalog(item_id):
	catalog = session.query(CatalogDB).filter_by(item_id = item_id).one()
	catalog_list = session.query(ItemsDB).filter_by(category_name = catalog.category_name).all()
	user_email = login_session['email']
	if 'username' not in login_session:
		login_status = ""
	else:
		login_status = login_session['email']
	return render_template('viewcatalog.html', catalog = catalog, catalog_list = catalog_list, login_status = login_status,user_email = user_email)
		
@app.route('/newcatalog/<int:item_id>/')
def NewCatalogItem(item_id):
	#check for user login incase the user goes to this url directly
	if 'username' not in login_session:
		return redirect ('/login')
	else:
		login_status = login_session['email']
	#Item_id in CatalogDB must not equal  item_id in ItemsDB
	catalog_Item_id = item_id
	catalog = session.query(CatalogDB).filter_by(item_id = item_id).one()
	category_name = catalog.category_name
	item_creator = login_session['email']
	#generate unique item_id for rows in ItemsDB
	item_id = random.randrange(10, 50000, 5)
	return render_template('newpost.html', login_status = login_status, item_creator = item_creator, item_id = item_id, category_name = category_name, catalog_Item_id = catalog_Item_id  )


@app.route('/savecatalog/<int:item_id>/', methods = ['GET', 'POST'])
def NewCatalogPost(item_id):
	if 'username' not in login_session:
		return redirect ('/login')
	elif request.method == 'POST':
		catalog_Item_id = item_id
		newItem = ItemsDB(category_name = request.form['category_name'], category_item = request.form['category_item'], item_id = request.form['item_id'], item_description= request.form['item_description'], item_creator= request.form['item_creator'])
		session.add(newItem)
		session.commit()
		flash("New Item Added Succesfully!")
		login_status = login_session['email']
		return redirect(url_for('ViewCatalog',item_id= catalog_Item_id, login_status= login_status))


@app.route('/viewitem/<int:item_id>/')
def ViewItem(item_id):
	login_status = login_session['email']
	item = session.query(ItemsDB).filter_by(item_id = item_id).one()
	return render_template('viewitem.html', item = item, login_status = login_status)

#Delete Item in a Catalog
@app.route('/deletecatalog/<int:item_id>/')
def DeleteCatalog(item_id):
	if 'username' not in login_session:
		return redirect ('/login')
	deleteItem = session.query(ItemsDB).filter_by(item_id = item_id).one()
	catalog = session.query(CatalogDB).filter_by(category_name = deleteItem.category_name).one()
	catalog_Item_id = catalog.item_id
	login_status = login_session['email']
	if GetItemCreator(item_id) == login_session['email']:
		session.delete(deleteItem)
		session.commit()
		flash("Item deleted successfully!")
		return redirect(url_for('ViewCatalog',item_id= catalog_Item_id, login_status = login_status))
	else:
		flash("NOT ALLOWED - You can only delete your creation!")
		return redirect(url_for('ViewCatalog',item_id= catalog_Item_id, login_status = login_status))

#Edit Item in a Catalog
@app.route('/editcatalog/<int:item_id>/', methods = ['GET', 'POST'])
def EditCatalog(item_id):
	if 'username' not in login_session:
		return redirect ('/login')
	login_status = login_session['email']
	if request.method == 'POST':
		if GetItemCreator(item_id) == login_session['email']:
			editItem = session.query(ItemsDB).filter_by(item_id = item_id).one()
			editItem.category_item = request.form['category_item']
			editItem.item_description = request.form['item_description']
			session.add(editItem)
			session.commit()
			flash("Item editted successfully!")
		else:
			flash("NOT ALLOWED - You can only edit your creation!")
		catalog = session.query(CatalogDB).filter_by(category_name = request.form['category_name']).one()
		catalog_Item_id = catalog.item_id
		return redirect(url_for('ViewCatalog',item_id= catalog_Item_id, login_status = login_status))
	else:
		editItem = session.query(ItemsDB).filter_by(item_id = item_id).one()
		return render_template('editcatalog.html', login_status = login_status, item_creator = editItem.item_creator, item_id = editItem.item_id, category_name = editItem.category_name, category_item = editItem.category_item, item_description = editItem.item_description  )

def GetItemCreator(item_id):
	try:
		getCreator = session.query(ItemsDB).filter_by(item_id = item_id).one()
		getCreator = getCreator.item_creator
		return getCreator
	except:
		return none

		
if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8080)