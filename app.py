from flask import Flask, render_template, request, redirect, make_response
from flask_bcrypt import Bcrypt

import datetime
import pytz
from urllib.parse import urlparse
import requests

from db import Database, hash_img
db = Database('db.xlsx')

from activities.fishing import Fishing

app = Flask(__name__)
bcrypt = Bcrypt(app)

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

@app.route("/edit-profile")
def edit_profile():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route("/change-password", methods=["POST"])
def change_password():
    user = authentication_check(request)
    if not user:
        return redirect("login")

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")

    # 1. Check current_password is correct
    if not bcrypt.check_password_hash(user.password, current_password):
        return render_template(
           "edit_profile.html",
            user=user,
            error="Current password is incorrect"
        )

    # 2. Check that new password is at least 8 characters
    if not len(new_password) >= 8:
        return render_template(
           "edit_profile.html",
            user=user,
            error="New password must be at least 8 characters"
        )

    # If the request passes both checks, get the new password hash write to db
    new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.update_user_password(user, new_password_hash)

    db.end_session(user.username)

    return render_template(
        "success.html",
        type='password_change',
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

    if token.disabled:
        return redirect("/")

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
            
            if not user or not bcrypt.check_password_hash(user.password, password):
                return render_template("login.html", error="Invalid username or password")
            session = db.start_session(username)

            response = make_response(redirect('/wallet'))
            response.set_cookie('session', session.token, expires=session.expires)
            return response

@app.route("/signup")
def signup():
    return render_template(
        'signup.html',
        state='invited'
    )


@app.route("/create-account", methods=["POST"])
def create_account():

    username = request.form.get("username").lower()
    nickname = request.form.get("nickname")
    password = request.form.get("password")

    # Check username is >= 3 char
    if not len(username) >= 3:
        return render_template(
            'signup.html',
            state='invited',
            error='Username must be at least 3 characters'
        )
    # Check username is < 255 char
    if not len(username) < 255:
        return render_template(
            'signup.html',
            state='invited',
            error='Username cannot be more than 255 characters'
        )

    # Check nickname is >= 3 char
    if not len(nickname) >= 3:
        return render_template(
            'signup.html',
            state='invited',
            error='Nickname must be at least 3 characters'
        )
    # Check nickname is < 255 char
    if not len(nickname) < 255:
        return render_template(
            'signup.html',
            state='invited',
            error='Nickname cannot be more than 255 characters'
        )

    # Check password is > 8 char
    if not len(password) >= 3:
        return render_template(
            'signup.html',
            state='invited',
            error='Password must be at least 8 characters'
        )
    # Check password is < 255 char
    if not len(password) < 255:
        return render_template(
            'signup.html',
            state='invited',
            error='Password cannot be more than 255 characters'
        )

    # Check username is not already taken
    if username in db.all_usernames():
        return render_template(
            'signup.html',
            state='invited',
            error='Sorry, that username is already taken'
        )

    # Check nickname is not already taken
    if nickname in db.all_nicknames():
        return render_template(
            'signup.html',
            state='invited',
            error='Sorry, that display name is already taken'
        )
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create account
    db.create_account(username, password_hash, nickname)

    # Login user
    user = db.get_user(username)
    session = db.start_session(username)

    # Return success page
    response = make_response(
        render_template(
            "success.html",
            type='signup',
            user=user
        )
    )
    response.set_cookie('session', session.token, expires=session.expires)
    return response

@app.route("/logout")
def logout():
    user = authentication_check(request)
    db.end_session(user.username)
    return redirect("/")

@app.route("/fishing")
def fishing():
    fishing = Fishing(db)
    return render_template(
        "fishing.html",
        fishing=fishing
    )

@app.route("/fishing/<location>")
def fishing_location(location):

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    fishing = Fishing(db)

    # If requested location doesn't exist
    if not hasattr(fishing, location):
        return render_template(
            "fishing.html"
        )

    # Otherwise render the location!
    return render_template(
        "fishing_location.html",
        location=getattr(fishing, location),
        user=user
    )

@app.route("/fishing/species/<species>")
def fishing_species(species):

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    fishing = Fishing(db)

    if not species in fishing.species:
        return redirect('/collection-log')

    species = fishing.species[species]

    return render_template(
        "fishing_species.html",
        user=user,
        stats=user.fish_catches_species_stats(species.name),
        species=species
    )

@app.route("/fishing/<location>/catch")
def fishing_catch(location):

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    fishing = Fishing(db)

    # If requested location doesn't exist, return an error
    if not hasattr(fishing, location):
        return render_template(
            "fishing.html"
        )

    if user.fished_today >= fishing.fishing_attempts_allowed:
        return render_template(
            "fishing_location.html",
            error=f"You caught {fishing.fishing_attempts_allowed} fish today. Return tomorrow!",
            location=getattr(fishing, location),
            user=user
        )

    # If user is logged in AND haven't caught a fish today, generate a new fish!
    fish = getattr(fishing, location).drop_table.get_drop()

    # Record the catch
    db.write_fish_catch(
        species=fish.species.name,
        weight_lbs=fish.weight_lbs,
        length_in=fish.length_in,
        angler_id=user.id,
        location_id=location
    )

    # Then send the LBC
    db.write_transaction(
        user_from=0,
        user_to=user.id,
        amount=fish.species.value_lbc
    )

    return render_template(
        "fish_catch.html",
        fish=fish,
        user=user
    )

@app.route("/collection-log")
def collection_log():

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    fishing = Fishing(db)

    return render_template(
        "collection_log.html",
        user=user,
        fishing=fishing
    )

@app.route("/ledger")
def ledger():
    user = authentication_check(request)
    return render_template(
        "ledger.html",
        transactions=db.transaction_list()
    )

@app.route("/studio")
def studio():
    return render_template(
        "studio.html"
    )

@app.route("/studio/create")
def studio_create():

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    return render_template(
        "studio_create.html"
    )

@app.route("/token-submission", methods=["POST"])
def token_submission():

    user = authentication_check(request)
    if not user:
        return redirect("/login")

    ###############

    # Check title was submitted
    if not 'title' in request.form:
        return render_template("studio_create.html", error="Title is required.")
    title = request.form.get("title")

    # Check URL was submitted
    if not 'url' in request.form:
        return render_template("studio_create.html", error="URL is required.")
    url = request.form.get("url")

    ###############

    # Check if user has already submitted a token this week
    if user.submissions_this_week > 0:
        return render_template("studio_create.html", error="You submitted a token this week. Try later!" , title=title, url=url)

    ###############

    # Check title doesn't contain any special characters
    special_characters = "@#$%^&*()-+?_=,<>{}`~[]:|'/\"\\"
    if '' or any(c in special_characters for c in title):
        return render_template("studio_create.html", error="Title can't contain special characters.", title=title, url=url)
    
    # Check title is less than 40 characters
    if len(title) >= 40:
        return render_template("studio_create.html", error="Title must be less than 40 characters.", title=title, url=url)

    # Check existing token doesn't already have this title
    if title in db.get_all_token_titles():
        return render_template("studio_create.html", error="Another token already has this title.", title=title, url=url)
    
    ###############

    # Check this exact url hasn't already been submitted
    if  url in db.get_all_token_urls():
        return render_template("studio_create.html", error="This image has already been submitted.", title=title, url=url)

    # Check url has a valid scheme
    url = urlparse(url)
    if not url.scheme == 'https' or url.scheme == 'http':
        return render_template("studio_create.html", error="Please submit a properly formatted url.", title=title, url=url.geturl())

    # Check file is .jpg
    extension = url.path.split('.')[-1]
    if not extension in ['jpg', 'JPG', 'jpeg', 'JPEG']:
        return render_template("studio_create.html", error="You can only submit JPG images.", title=title, url=url.geturl())

    # Check url isn't broken
    rsp = requests.get(
        url.geturl(), 
        stream=True,
        headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        }
    )
    if not rsp.ok:
        return render_template("studio_create.html", error="That url is broken. Please try again!", title=title, url=url.geturl())

    # Check existing token doesn't already have this hash!
    img_hash = hash_img(url.geturl())
    if img_hash in db.get_all_token_hashes():
        return render_template("studio_create.html", error="This image has already been submitted.", title=title, url=url.geturl())

    ##########################################

    # If the submission passes all the above checks, the submission is created!

    db.write_new_token_submission(
        token_note=title,
        token_url=url.geturl(),
        token_hash=img_hash,
        token_author_id=user.id
    )

    return render_template(
        "success.html",
        type='submission'
    )

@app.route("/submissions")
def submissions():

    user = authentication_check(request)
    if not user:
        return redirect("login")
    
    if not user.admin:
        return redirect("/")
        
    return render_template(
        "submissions.html",
        submissions=db.pending_submissions()
    )

@app.route("/submission-review", methods=["POST"])
def submission_review():

    user = authentication_check(request)
    if not user:
        return redirect("login")
    
    if not user.admin:
        return redirect("home")
    
    submission_id = int(request.form.get("submission_id"))
    action = request.form.get("action")

    match action:
        case 'approve':
            db.submission_approve(submission_id)
        case 'deny':
            db.submission_deny(submission_id)

    return render_template(
        "success.html",
        type='submission_'+action,
        submission=db.submissions[submission_id]
    )

@app.route("/submission-review-confirmation", methods=["POST"])
def submission_review_confirmation():

    user = authentication_check(request)
    if not user:
        return redirect("login")
    
    if not user.admin:
        return redirect("home")
    
    submission_id = int(request.form.get("submission_id"))
    review_type = request.form.get("type")

    return render_template(
        "submission_review_confirmation.html",
        type=review_type,
        submission=db.submissions[submission_id]
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
                return render_template("send_lbc.html", user=user_from, users=db.user_list(user_from), error="Can't send negative LBC.")

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
def format_day(d):
    eastern = pytz.timezone('US/Eastern')
    dt = datetime.datetime.fromisoformat(d).replace(tzinfo=datetime.UTC)
    return dt.astimezone(eastern).strftime("%b %-d, %Y")

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
    if d == 0:
        return '-'

    lb = int(d) # Number of whole lbs
    oz = int(   # Number of whole oz
        (d % 1) * 16
    )
    return f'{lb} lbs {oz} oz'

@app.template_filter()
def format_fish_length(d):
    if d == 0:
        return '-'

    return f'{round(d,1)} in'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
