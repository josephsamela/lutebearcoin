from flask import Flask, render_template, request, redirect, make_response, jsonify

import datetime
import pytz

from db import Database
db = Database('db.xlsx')

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    user = authentication_check(request)
    return render_template(
        "home.html", 
        user=user
    )

@app.route("/wallet")
def wallet():
    user = authentication_check(request)
    if not user:
        return redirect("login")
    return render_template(
        "wallet.html", 
        user=user
    )

@app.route("/leaderboard")
def leaderboard():
    users = list(db.users.values())
    users = users[1:]
    users = sorted(users, key=lambda x: x.balance, reverse=True)
    return render_template(
        "leaderboard.html", 
        users=users
    )

@app.route("/user/<username>")
def user(username):
    user = db.get_user(username)
    return render_template(
        "user.html", 
        user=user
    )

@app.route("/token/<token_id>")
def token(token_id):
    token_id = int(token_id)
    token = db.get_token(token_id)
    return render_template(
        "token.html", 
        token=token
    )

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    match request.method:
        case 'GET':
            return render_template("login.html")
        case 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            user = db.get_user(username)
            
            if not user or user.password != password:
                return render_template("login.html", error="Invalid username or password")
            session = db.start_session(username)

            response = make_response(redirect('/wallet'))
            response.set_cookie('session', session.token, expires=session.expires)
            return response

@app.route("/logout")
def logout():
    user = authentication_check(request)
    db.end_session(user.username)
    return redirect("/")

@app.route("/transactions")
def transactions():
    user = authentication_check(request)
    return render_template(
        "transactions.html",
        transactions=db.transaction_list()
    )

@app.route("/transaction", methods=["POST"])
def transaction():

    user_from = authentication_check(request)
    if not user_from:
        return redirect("login")

    transaction_type = request.form.get("transaction_type")
    user_to = request.form.get("to")

    match transaction_type:

        # This route supports two types of transactions:
        #   1. "lbc" = Send an amount of lbc to a recipient.
        #   2. "nft" = Send a nft to a recipient.

        case 'lbc':
            transaction_amount = request.form.get("amount")

            # Validation Checks

            if not int(transaction_amount):
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Can only send whole number of LBC.")

            if '.' in transaction_amount:
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Can only send whole number of LBC.")

            if not db.get_user(user_to):
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Recipient does not exist.")

            if int(transaction_amount) > user_from.balance:
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Insufficient balance")

            db.write_transaction(
                user_from=user_from.id,
                user_to=db.get_user(user_to).id,
                amount=int(transaction_amount)
            )

            return make_response(redirect('success'))

        case 'nft':

            transaction_token = request.form.get("token")

            if not db.get_user(user_to):
                return render_template("send_nft.html", user=user_from, users=db.user_list(user), error="Recipient does not exist.")

            if not int(transaction_token):
                return render_template("send_nft.html", user=user_from, users=db.user_list(user), error="You can only send Tokens you own.")

            if not int(transaction_token) in user_from.tokens:
                return render_template("send_nft.html", user=user_from, users=db.user_list(user), error="You can only send Tokens you own.")

            db.write_transaction(
                user_from=user_from.id,
                user_to=db.get_user(user_to).id,
                token=transaction_token
            )

            return make_response(redirect('success'))

        case _:
            return redirect("wallet")

@app.route("/send_lbc")
def send_lbc():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    return render_template("send_lbc.html", user=user, users=db.user_list(user))

@app.route("/send_nft")
def send_nft():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    return render_template("send_nft.html", user=user, users=db.user_list(user))

@app.route("/success")
def success():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    return render_template(
        "success.html", 
        user=user
    )

def authentication_check(request):
    # Check if browser session exists.
    session = request.cookies.get('session')
    # Check if user exists.
    user = db.check_session(session)
    return user

@app.template_filter()
def format_date(d):
    eastern = pytz.timezone('US/Eastern')
    dt = datetime.datetime.fromisoformat(d).replace(tzinfo=datetime.UTC)
    return dt.astimezone(eastern).strftime("%b %-d, %Y %-I:%M %p")

@app.template_filter()
def format_credit_date(d):
    dt = datetime.datetime.fromisoformat(d)
    return dt.strftime("%m/%Y")

@app.template_filter()
def format_account_number(d):
    
    account_id = ''

    r = 16 - len(str(d))
    d = '0'*r + str(d)

    c = 0
    for i in d:
        account_id += i
        c += 1
        if c == 4:
            account_id += ' '
            c = 0
    return account_id

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
