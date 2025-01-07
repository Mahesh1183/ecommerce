from http import client
from flask import Flask,render_template,request,flash,session,redirect,url_for
import mysql.connector
import razorpay
from otp import genotp
from itemid import itemidotp
from cmail import sendemail
from adminmail import adminsendmail
from adminotp import adotp
import os
RAZORPAY_KEY_ID='rzp_test_rnAwL12OAsSYxV'
RAZORPAY_KEY_SECRET=''
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
# mydb=mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='root',
#     database='ecommerce'
# )
app=Flask(__name__)
app.secret_key='hfbfe78hjefk'
@app.route('/')
def base():
    return render_template('homepage.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=="POST":
        name=request.form['name']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password'] 
        cursor=mydb.cursor()
        cursor.execute('select email from signup')
        data=cursor.fetchall()
        cursor.execute('select mobile from signup')
        edata=cursor.fetchall()
        if(mobile,) in edata:
            flash('User already exist')
            return render_template('register.html')
        if(email,)in data:
            flash('Email address already exists')
            return render_template('register.html')
        cursor.close()
        otp=genotp()
        subject='thanks for registering to the application'
        body=f'use this otp to register {otp}'
        sendemail(email,subject,body)
        return render_template('otp.html',otp=otp,name=name,mobile=mobile,email=email,address=address,password=password)
    else:
        return render_template('register.html')
@app.route('/otp/<otp>/<name>/<mobile>/<email>/<address>/<password>',methods=['GET','POST'])
def otp(otp,name,mobile,email,address,password):
    if request.method=="POST":
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mydb.cursor()
            lst=[name,mobile,email,address,password]
            query='insert into signup values(%s,%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,name=name,mobile=mobile,email=email,address=address,password=password)
        
@app.route('/adminregister',methods=['GET','POST'])
def adminregister():
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form.get('mobile')
        email=request.form.get('email')
        password=request.form.get('password')
        cursor=mydb.cursor()
        cursor.execute('select email from signup')
        data=cursor.fetchall()
        cursor.execute('select mobile from signup')
        edata=cursor.fetchall()
        #print(data)
        if (mobile, ) in edata:
            flash('User already exisit')
            return render_template('adminregister.html')
        if (email, ) in data:
            flash('Email id already exisit')
            return render_template('adminregister.html')
        if not email:
            return "Invalid email address", 400

        cursor.close()
        adminotp=adotp()
        subject='thanks for registering to the application'
        body=f'use this adminotp to register {adminotp}'
        sendemail(email,subject,body)
        return render_template('adminotp.html',adminotp=adminotp,name=name,mobile=mobile,email=email,password=password)
    else:
        return render_template('adminregister.html')

@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method == 'POST':
        email=request.form['mail']
        password=request.form['pswd']
        print(email)
        print(password)
        cursor=mydb.cursor()
        cursor.execute('select count(*) from admindata where mail=%s and passcode=%s',[email,password])
        count=cursor.fetchone()
        print(count)
        if count==0:
            flash("Invalid email or password")
            return render_template('adminlogin.html')
        else:
            session['mail']=email
            if not session.get(email):
                session[email]={}
            return redirect(url_for('admindashboard'))
    return render_template('adminlogin.html')

@app.route('/adminotp/<adminotp>/<name>/<mobile>/<email>/<password>',methods=['GET','POST'])
def adminotp(adminotp,name,mobile,email,password):
    if request.method=='POST':
        uotp=request.form['adminotp']
        if adminotp==uotp:
            cursor=mydb.cursor()
            lst=[name,mobile,email,password]
            query='insert into adminsignup values(%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('adminlogin'))
        else:
            flash('Wrong otp')
            return render_template('adminotp.html',adminotp=adminotp,name=name,mobile=mobile,email=email,password=password)

@app.route('/admindashboard',methods=['GET','POST'])
def admindashboard():
    return render_template('admindashboard.html')

@app.route('/adminlogout')
def adminlogout():
    if session.get('mail'):
        session.pop('mail')
        return redirect(url_for('home'))
    else:
        flash("Already logged out!")
        return redirect(url_for('adminlogin'))
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select count(*) from signup where username=%s \
        and password=%s',[username,password])
        count=cursor.fetchone()[0]
        print(count)
        if count==0:
            flash('Invalid email or password')
            return render_template('login.html')
        else:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for('base'))
    return render_template('login.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('base'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
@app.route('/additems', methods=['GET', 'POST'])
def additems():
    if request.method == 'POST':
        name=request.form['name']
        description=request.form['description']
        quantity=request.form['quantity']
        category=request.form['category']
        price=request.form['price']
        image=request.files['image']
        # Valid categories from ENUM
        valid_categories = ['electronics', 'grocery', 'fashion', 'home']
        # Validate category input
        if category not in valid_categories:
            flash("Invalid category. Please select a valid option.")
            return render_template('items.html')
        cursor = mydb.cursor()
        idotp = itemidotp()  # Function to generate unique item ID
        filename = idotp + '.jpg'
        # Insert the validated data into the database
        cursor.execute(
            'INSERT INTO additems (itemid, name, description, qty, category, price) VALUES (%s, %s, %s, %s, %s, %s)',
            [idotp, name, description, quantity, category, price]
        )
        mydb.commit()
        # Save the uploaded image
        path = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(path, 'static')
        image.save(os.path.join(static_path, filename))
        flash('Item added successfully!')
    return render_template('items.html')

@app.route('/homepage')
def homepage():
    return render_template('homepage.html')

@app.route('/dashboardpage')
def dashboardpage():
    cursor=mydb.cursor()
    cursor.execute("select * from additems")
    items=cursor.fetchall()
    print(items)
    return render_template('dashboard.html',items=items)

@app.route('/status')
def status():
    cursor=mydb.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    return render_template('status.html',items=items)

@app.route("/updateproducts/<itemid>",methods=['GET','POST'])
def updateproducts(itemid):
    print(itemid)
    cursor=mydb.cursor()
    cursor.execute('select name,description,qty,category,price from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    cursor.close()
    if request.method=="POST":
        name=request.form['name']
        description=request.form['desc']
        quantity=request.form['quantity']
        category=request.form['category']
        price=request.form['price']
        cursor=mydb.cursor()
        cursor.execute('update additems set name=%s,description=%s,quantity=%s,category=%s,price=%s where itemid=%s',[name,description,quantity,category,price,itemid])
        mydb.commit()
        cursor.close()
    return render_template('updateproducts.html',items=items)

@app.route('/deleteproducts/<itemid>',methods=['GET','POST'])
def deleteproducts(itemid):
    cursor=mydb.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mydb.commit()
    cursor.close()
    path=os.path.dirname(os.path.abspath(__file__))
    static_path=os.path.join(path,'static')
    filename=itemid+'.jpg'
    os.remove(os.path.join(static_path,filename))
    flash("Deleted")
    return redirect(url_for('status'))

@app.route('/index')
def index():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT itemid, name, quantity, category, price FROM additems')
    item_data = cursor.fetchall()
    print(item_data)
    return render_template('index.html', item_data=item_data)

@app.route('/addcart/<itemid>/<name>/<category>/<price>/<quantity>',methods=['GET','POST'])
def addcart(itemid,name,category,price,quantity):
    if not session.get('user'):
        return redirect(url_for('login'))
    else:
        print(session)
        if itemid not in session.get(session['user'],{}):
            if session.get(session['user']) is None:
                session[session['user']]={}
            session[session['user']][itemid]=[name,price,1,f'{itemid}.jpg',category]
            session.modified=True
            flash(f'{name} added to cart')
            return redirect(url_for('index'))
        session[session['user']][itemid][2]+=1
        session.modified=True
        flash(f'{name} quantity increased in the cart')
        return redirect(url_for('index'))

@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    user_cart=session.get(session.get('user'))
    if not user_cart:
        items='empty'
    else:
        items=user_cart
    if items=='empty':
        return '<h3 Your cart is empty </h3>'
    return render_template('cart.html',items=items)

@app.route('/cartpop/<itemid>')
def cartpop(itemid):
    print(itemid)
    if session.get('user'):
        print(session)
        session[session.get('user')].pop(itemid)
        session.modified=True
        flash('items removed')
        print(session)
        return redirect(url_for('viewcart'))
    else:
        return redirect(url_for('login'))
    
@app.route('/dis/<itemid>')
def dis(itemid):
    cursor=mydb.cursor()
    cursor.execute('select * from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    return render_template('description.html',items=items)

@app.route('/category/<category>')
def category(category):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select*from additems where category =%s',[category])
        data=cursor.fetchall()
        cursor.close()
        return render_template('category.html',data=data)
    else:
        return redirect( url_for('login'))
    
@app.route('/pay/<itemid>/<name>/<int:price>', methods=['POST'])
def pay(itemid, name, price):
    try:
        # Get the quantity from the form
        quantity = int(request.form['quantity'])

        # Calculate the total amount in paise (price is in rupees)
        total_price = int(price) * quantity  # Ensure integer multiplication

        print(f"Creating payment for Item ID: {itemid}, Name: {name}, Total Price: {total_price}")

        # Create Razorpay order
        order = client.order.create({
            'amount': total_price,
            'currency': 'INR',
            'payment_capture': '1'
        })

        print(f"Order created: {order}")
        return render_template('pay.html', order=order, itemid=itemid, name=name, price=total_price, quantity=quantity)
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return str(e), 400

@app.route('/success',methods=['POST'])
def success():
    payments_id=request.form.get('razorpay_payment_id')
    order_id=request.form.get('razorpay_order_id')
    signature=request.form.get('razorpay_signature')
    name=request.form.get('name')
    itemid=request.form('itemid') 
    total_price=request.form('total_price')
    quantity=request.form('quantity')
    
    params_dict={
        'razorpay_payment_id'
        'razorpay_order_id'
        'razorpay_signature'
    }  
    try:
        client.utility.verify_payments_signature(params_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,total_price,user,quantity)values(%s,%s,%s,%s,%s)',[itemid.name,total_price,session.get('user'),quantity])
        mydb.commit()
        cursor.close()
        flash('orders placed successfully')
        return 'orders'
    except razorpay.errors.SignatureVerificationError:
        return 'payments verification failed',400

app.run(debug=True,use_reloader=True)
