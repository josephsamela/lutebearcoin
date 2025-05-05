import openpyxl
import datetime
import uuid
import json

class Database:
    def __init__(self, path):
        self.path = path
        self.workbook = openpyxl.load_workbook(path)
        self.sessions = {}

        self.load_db()

    def load_db(self):
        self.users = self.load_data(self.workbook, 'users', User)
        self.tokens = self.load_data(self.workbook, 'tokens', Token)
        self.transactions = self.load_data(self.workbook, 'transactions', Transaction)

    def write_transaction(self, user_from, user_to, amount=0, token=None ):
        worksheet=self.workbook['transactions']

        if token:
            worksheet.append([
                max(self.transactions.keys())+1,
                datetime.datetime.now().isoformat(),
                user_from,
                user_to,
                None,
                int(token)
            ])

        else:
            worksheet.append([
                max(self.transactions.keys())+1,
                datetime.datetime.now().isoformat(),
                user_from,
                user_to,
                int(amount),
                None
            ])

        self.workbook.save(self.path)
        self.load_db()

    def load_data(self, workbook, worksheet, pattern):
        first = True
        headers = None
        data = {}
        for i, row in enumerate(workbook[worksheet].iter_rows(values_only=True)):
            if first:
                headers = row
                first = False
            else:
                rowdict = dict()
                for i, header in enumerate(headers):
                    rowdict[header] = row[i]
                obj = pattern(rowdict, self)
                data[obj.id] = obj
        return data
        
    def get_user(self, username):
        for id,user in self.users.items():
            if user.username == username:
                return user
        return None
    
    def get_token(self, token_id):
        for id,token in self.tokens.items():
            if token.id == token_id:
                return token
        return None

    def start_session(self, username):
        session = Session(username)
        self.sessions[username] = session
        return session

    def end_session(self, username):
        self.sessions.pop(username)

    def check_session(self, token):
        for id,session in self.sessions.items():
            if session.token == token:
                return self.get_user(session.username)
        return None

    def user_list(self, user):
        users = []
        for id,u in self.users.items():
            if u.username == 'system':
                continue
            if u.username == user.username:
                continue
            users.append(u.username)
        return users

    def generate_new_id(self):
        from random import randint
        s = ''
        for i in range(16):
            s = s + str(randint(0,9))
        return s

class Object:
    def __init__(self, d, db):
        self.db = db
        for key in d:
            setattr(self, key, d[key])

    def __iter__(self):
        for p in dir(self):
            if not p.startswith('__'):
                yield p, getattr(self, p)

    def __repr__(self):
        d = {}
        for p in dir(self):
            if p.startswith('__'):
                continue
            if p == 'db':
                continue

            if type(getattr(self, p)) == User:
                d[p] = dict(getattr(self, p))
            else:
                d[p] = getattr(self, p)

        return json.dumps(d)

def safe_serialize(obj):
  default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>"
  return json.dumps(obj, default=default)

class User(Object):

    @property
    def tokens(self):
        tokens = {}
        for id, transaction in self.db.transactions.items():

            if transaction.amount:
                continue

            if getattr(transaction, 'to') is self.id:
                tokens[transaction.token] = self.db.tokens[transaction.token].to_dict()

            if getattr(transaction, 'from') is self.id:
                if transaction.token in tokens:
                    tokens.pop(transaction.token)

        return tokens

    @property
    def balance(self):
        balance = 0

        for id, transaction in self.db.transactions.items():

            if not transaction.amount:
                continue

            if getattr(transaction, 'to') is self.id:
                balance += transaction.amount

            if getattr(transaction, 'from') is self.id:
                
                if getattr(transaction, 'to') == getattr(transaction, 'from') and self.id == 0:
                    continue

                balance -= transaction.amount
        
        return balance
    
    @property
    def transactions(self):
        transactions = []

        for id, transaction in self.db.transactions.items():

            if getattr(transaction, 'to') is self.id:
                transactions.append(transaction.to_dict())

            if getattr(transaction, 'from') is self.id:
                transactions.append(transaction.to_dict())

        transactions.reverse()

        return transactions

    def to_dict(self):
        d = {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'created_at': self.created_at,
            'balance': self.balance,
            'transactions': self.transactions,
            'tokens': self.tokens
        }
        return d

class Token(Object):

    @property
    def owner(self):
        owner = None
        for id, transaction in self.db.transactions.items():

            if transaction.amount:
                continue

            if transaction.token is self.id:
                owner = self.db.users[transaction.to]

        return owner
    
    @property
    def transactions(self):
        t = []
        for id, transaction in self.db.transactions.items():
            if transaction.token is self.id:
                t.append(transaction)
        t.reverse()
        return t

    def to_dict(self):
        d = {
            'id': self.id,
            'created_at': self.created_at,
            'note': self.note,
            'url': self.url
        }
        return d

class Transaction(Object):

    @property
    def user_from(self):
        return self.db.users[getattr(self, 'from')]

    @property
    def user_to(self):
        return self.db.users[getattr(self, 'to')]
    
    def to_dict(self):
        d = {
            'id': self.id,
            'timestamp': self.timestamp,
            'amount': self.amount,
            'token': self.token,
            'user_from_id': self.user_from.id,
            'user_from_username': self.user_from.username,
            'user_from_nickname': self.user_from.nickname,
            'user_to_id': self.user_to.id,
            'user_to_username': self.user_to.username,
            'user_to_nickname': self.user_to.nickname,
            'token_url': None,
            'token_note': None

        }
        if self.token:
            d['token_url'] = self.db.tokens[self.token].url
            d['token_note'] = self.db.tokens[self.token].note

        return d

class Session:
    def __init__(self, username):
        self.username = username
        self.expires = datetime.datetime.now() + datetime.timedelta(days=30)
        self.token = str(uuid.uuid4())
