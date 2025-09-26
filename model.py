import datetime
from peewee import *

db = SqliteDatabase('db.sqlite')

class Base(Model):
    class Meta:
        database = db

class Player(Base):
    '''
    Player

    id              Number      Player record ID
    username        String      Player username
    password        String      Player password hash
    created_at      DateTime    Timestamp when the account was created
    admin           Boolean     Controls if user has admin permissions
    '''
    created_at = DateTimeField(default=datetime.datetime.now())
    username = CharField(unique=True)
    password = CharField()
    admin = BooleanField(default=False)

class Item(Base):
    '''
    Item
    '''
    name = CharField(unique=True)
    stackable = BooleanField(default=True)

class Inventory(Base):
    '''
    Inventory
    '''
    player = ForeignKeyField(Player)
    item = ForeignKeyField(Item)
    quantity = IntegerField()

class Skill(Base):
    '''
    Skill
    '''
    name = CharField(unique=True)
    
class Experience(Base):
    '''
    Experience
    '''
    player = ForeignKeyField(Player)
    skill = ForeignKeyField(Skill)
    experience = IntegerField()

class Token(Base):
    created_at = DateTimeField(default=datetime.datetime.now())
    title = CharField()
    link = CharField()
    hidden = BooleanField(default=False)

class Transactions(Base):
    '''
    Transaction

    Represents one transaction.
    '''
    created_at = DateTimeField(default=datetime.datetime.now())
    from_player_id = ForeignKeyField(Player)
    to_player_id = ForeignKeyField(Player)
    amount = IntegerField()
    token = ForeignKeyField(Token)


if __name__ == '__main__':

    # Database Init Test

    db.connect()
    db.create_tables([Player, Item, Skill, Experience, Inventory])

    Player.create(username='joe', password='12345')
    Player.create(username='jamie', password='12345')

    Item.create(name='Bait', stackable=True)
    Item.create(name='Fishing Rod', stackable=False)

    Skill.create(name='Fishing')

    # 

    joe = Player.get(Player.username == 'joe')
    bait = Item.get(Item.name =='bait')
    fishing = Skill.get(Skill.name == 'Fishing')

    Inventory.create(
        player=joe,
        item=bait,
        quantity=10
    )

    Experience.create(
        player=joe,
        skill=fishing,
        experience=10
    )


