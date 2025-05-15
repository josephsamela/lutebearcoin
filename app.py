from flask import Flask, render_template, request, redirect, make_response, jsonify

import datetime
import pytz
from operator import attrgetter

from db import Database
db = Database('db.xlsx')

from activities.fishing import DropTable as FishingDropTable

app = Flask(__name__)

@app.route("/")
def home():
    user = authentication_check(request)
    return render_template(
        "home.html", 
        user=user
    )

@app.route("/about")
def about():
    return render_template(
        "about.html", 
    )

@app.route("/wallet")
def wallet():
    user = authentication_check(request)
    if not user:
        return redirect("login")
    tokens = list(user.tokens.values())
    return render_template(
        "wallet.html",
        tokens=tokens,
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

@app.route("/market")
def market():
    for_sale = list(db.for_sale().values())
    for_sale.reverse()
    return render_template(
        "market.html", 
        forsale=for_sale
    )

@app.route("/user/<username>")
def user(username):
    user = db.get_user(username)
    tokens = list(user.tokens.values())
    return render_template(
        "user.html", 
        user=user,
        tokens=tokens
    )

@app.route("/user/<username>/transactions")
def user_transactions(username):
    user = db.get_user(username)
    return render_template(
        "user_transactions.html",
        user=user
    )

@app.route("/user/<username>/tokens")
def user_tokens(username):
    user = db.get_user(username)
    return render_template(
        "user_tokens.html",
        user=user
    )

@app.route("/token/<token_id>")
def token(token_id):
    user = authentication_check(request)
    token_id = int(token_id)
    token = db.get_token(token_id)
    return render_template(
        "token.html", 
        token=token,
        user=user
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

@app.route("/fishing")
def fishing():

    catches = list(db.fish_catches.values())
    catches = sorted(catches, key=attrgetter('length_in', 'weight_lbs'), reverse=True)

    return render_template(
        "fishing.html",
        catches=catches
    )

@app.route("/fishing/catch", methods=["POST"])
def fishing_catch():

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    if not 'location' in request.form:
        return redirect("/login")
    location = request.form.get('location')

    if len(user.fish_catches) > 0:
        eastern = pytz.timezone('US/Eastern')
        last_fish_ts = datetime.datetime.fromisoformat(user.fish_catches[0].timestamp).replace(tzinfo=datetime.UTC).astimezone(eastern)

        if not last_fish_ts.date() < datetime.datetime.today().astimezone(eastern).date():
            catches = list(db.fish_catches.values())
            catches = sorted(catches, key=attrgetter('length_in', 'weight_lbs'), reverse=True)

            return render_template(
                "fishing.html",
                catches=catches,
                error="You caught a fish today. Return tomorrow!"
            )

    # If user is logged in AND haven't caught a fish today, generate a new fish!
    drop_table = FishingDropTable()
    fish = drop_table.get_drop()

    # Record the catch
    db.write_fish_catch(
        species=fish.species.name,
        weight_lbs=fish.weight_lbs,
        length_in=fish.length_in,
        angler_id=user.id
    )

    # Then send the LBC
    db.write_transaction(
        user_from=0,
        user_to=user.id,
        amount=fish.species.value_lbc
    )

    return render_template(
        "catch.html",
        fish=fish,
        user=user
    )

@app.route("/ledger")
def ledger():
    user = authentication_check(request)
    return render_template(
        "ledger.html",
        transactions=db.transaction_list()
    )

@app.route("/transaction", methods=["POST"])
def transaction():

    user_from = authentication_check(request)
    if not user_from:
        return redirect("login")

    transaction_type = request.form.get("transaction_type")

    match transaction_type:

        # This route supports three types of transactions:
        #   1. "lbc" = Send an amount of lbc to a recipient.
        #   2. "nft" = Send a nft to a recipient.
        #   3. "buy" = Buy a listed item

        case 'lbc':
            user_to = request.form.get("to")
            amount = request.form.get("amount")

            if not amount.isdigit():
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Can only send whole number of LBC.")

            amount = int(amount)

            if amount < 0:
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Cannot send negative LBC.")

            if not db.get_user(user_to):
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Recipient does not exist.")

            if amount > user_from.balance:
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Insufficient balance")

            db.write_transaction(
                user_from=user_from.id,
                user_to=db.get_user(user_to).id,
                amount=amount
            )

            return render_template("success.html", event=db.transactions[max(db.transactions.keys())], type="lbc")

        case 'nft':
            user_to = request.form.get("to")
            token_id = request.form.get("token")

            if not token_id.isdigit():
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="Invalid token.")
            
            token_id = int(token_id)

            if not token_id in db.tokens:
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="Token does not exist.")
            
            token = db.get_token(token_id)

            if not db.get_user(user_to):
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="Recipient does not exist.")

            if db.get_user(user_to).id == token.owner.id:
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="You can't send tokens to yourself.")

            if not token.id in user_from.tokens:
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="You can only send Tokens you own.")
            
            if token.for_sale:
                return render_template("send_nft.html", user=user_from, users=db.user_list(user_from), error="You can't send a token listed for sale.")

            db.write_transaction(
                user_from=user_from.id,
                user_to=db.get_user(user_to).id,
                token=token.id
            )

            return render_template("success.html", event=db.transactions[max(db.transactions.keys())], type="nft")

        case 'buy':

            token_id = request.form.get("token_id")

            # Check token id is in correct format
            if not token_id.isdigit():
                return render_template("purchase.html", token=token, error="Invalid token.")

            token_id = int(token_id)

            # Check token exists
            if not token_id in db.tokens:
                return render_template("purchase.html", token=token, error="Token does not exist.")

            token = db.get_token(token_id)

            # Check token is for sale
            if not token.for_sale:
                return render_template("purchase.html", token=token, error="Token is not for sale.")
            
            # Check buyer doesn't already own this item
            if token.id in user_from.tokens:
                return render_template("purchase.html", token=token, error="You already own this item.")

            # Check buyer has sufficient balance
            if user_from.balance < token.listing.amount:
                return render_template("purchase.html", token=token, error="Insufficient balance.")
            
            # Check it's not being purchased for a negative amount
            if token.listing.amount < 0:
                return render_template("purchase.html", token=token, error="Negative purchase amount.")

            # Send LBC from buyer to seller
            db.write_transaction(
                user_from=user_from.id,
                user_to=token.owner.id,
                token=None,
                amount=token.listing.amount
            )

            # Send NFT from seller to buyer
            db.write_transaction(
                user_from=token.owner.id,
                user_to=user_from.id,
                token=token.id,
                amount=None
            )

            # System removes for sale listing
            db.write_listing(
                seller_id=0,
                token_id=token.id,
                amount=None
            )

            return render_template("success.html", event=db.listings[max(db.listings.keys())], type="buy")

        case 'list':

            token_id = request.form.get("token_id")
            amount = request.form.get("amount")

            # Check token id is in correct format
            if not token_id.isdigit():
                return render_template("sell.html", token=token, error="Invalid token.")
            
            # Check amount is in correct format
            if not token_id.isdigit():
                return render_template("sell.html", token=token, error="Can only list in whole LBC.")

            token_id = int(token_id)
            amount = int(amount)

            # Check list amount is positive
            if amount < 0:
                return render_template("sell.html", token=token, error="Can't list for negative LBC.")

            # Check list amount doesn't exceed total amount of lbc
            if amount > 100000000:
                return render_template("sell.html", token=token, error="Must list for less than 100M LBC.")

            # Check token exists
            if not token_id in db.tokens:
                return render_template("sell.html", token=token, error="Token does not exist.")

            token = db.get_token(token_id)

            # Check token is not already for sale
            if token.for_sale:
                return render_template("sell.html", token=token, error="Token is already for sale.")
            
            # Check seller owns this item
            if not token.id in user_from.tokens:
                return render_template("sell.html", token=token, error="You don't own this item.")

            # Create Listing
            db.write_listing(
                seller_id=user_from.id,
                token_id=token.id,
                amount=amount
            )

            return render_template("success.html", event=db.listings[max(db.listings.keys())], type="list")
        
        case 'unlist':

            token_id = request.form.get("token_id")

            # Check token id is in correct format
            if not token_id.isdigit():
                return render_template("unlist.html", token=token, error="Invalid token.")
            
            token_id = int(token_id)

            # Check token exists
            if not token_id in db.tokens:
                return render_template("unlist.html", token=token, error="Token does not exist.")

            token = db.get_token(token_id)

            # Check token isn't not listed for sale
            if not token.for_sale:
                return render_template("unlist.html", token=token, error="Token is not listed for sale.")
            
            # Check seller owns this item
            if not token.id in user_from.tokens:
                return render_template("unlist.html", token=token, error="You don't own this item.")

            # Create Listing
            db.write_listing(
                seller_id=user_from.id,
                token_id=token.id,
                amount=None
            )

            return render_template("success.html", event=db.listings[max(db.listings.keys())], type="unlist")

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

@app.route("/sell", methods=["POST"])
def sell():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    token_id = request.form.get("token_id")
    if not token_id or not token_id.isdigit():
        return redirect("login")

    token = db.get_token(int(token_id))

    return render_template(
        "sell.html",
        token=token
    )

@app.route("/unlist", methods=["POST"])
def unlist():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    token_id = request.form.get("token_id")
    if not token_id or not token_id.isdigit():
        return redirect("login")

    token = db.get_token(int(token_id))

    return render_template(
        "unlist.html",
        token=token
    )

@app.route("/purchase", methods=["POST"])
def purchase():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    token_id = request.form.get("token_id")
    if not token_id or not token_id.isdigit():
        return redirect("login")

    token = db.get_token(int(token_id))

    if not token.for_sale:
        return redirect("login")

    return render_template(
        "purchase.html", 
        token=token
    )

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

@app.template_filter()
def format_fish_weight(d):
    lb = int(d) # Number of whole lbs
    oz = int(   # Number of whole oz
        (d % 1) * 16
    )
    return f'{lb} lbs {oz} oz'

@app.template_filter()
def format_fish_length(d):
    return f'{round(d,1)} in'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
