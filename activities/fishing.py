import random
from operator import attrgetter

class Location:
    def __init__(self, db, id, name, drop_table):
        self.db = db
        self.id = id
        self.name = name
        self.drop_table = drop_table

    @property
    def species(self):
        return self.drop_table.drops
    
    @property
    def catches(self):
        # Return list of catches from this location
        # Sorted by fish length. Longest -> Shortest
        c = []
        for id,catch in self.db.fish_catches.items():
            if catch.location_id == self.id:
                c.append(catch)
        return sorted(c, key=attrgetter('length_in'), reverse=True)

class DropTable:
    def __init__(self, drops, weights):
        self.drops   = drops
        self.weights = weights

    def get_drop(self):
        species = random.choices(self.drops, self.weights)[0]
        return Fish(species)

class Fish:
    def __init__(self, species):
        self.species = species
        self.weight_lbs = self._weight()
        self.length_in = self._length()

    @property
    def relative_size(self):
        # This property represents the "size" of the
        # fish relative to its maximum possible size.
        w = random.gauss(
            mu = 50,
            sigma = 13
        )
        if w > 100:
            return 100
        elif w < 5:
            return 5
        else:
            return w / 100

    def _weight(self):
        return self.relative_size * self.species.max_weight_lbs
        
    def _length(self):
        return self.relative_size * self.species.max_length_in

class FishSpecies:
    def __init__(self, 
            name,
            max_weight_lbs,
            max_length_in,
            icon,
            value_lbc
        ):
        self.name = name
        self.max_weight_lbs = max_weight_lbs
        self.max_length_in = max_length_in
        self.icon = icon
        self.value_lbc = value_lbc

# Create Species

salmon_pink = FishSpecies(
    name = 'Pink Salmon',
    max_weight_lbs=15,
    max_length_in=30,
    icon='salmon_pink.png',
    value_lbc = 1
)

salmon_coho = FishSpecies(
    name = 'Coho Salmon',
    max_length_in=42,
    max_weight_lbs=36,
    icon='salmon_coho.png',
    value_lbc=2
)

salmon_sockeye = FishSpecies(
    name = 'Sockeye Salmon',
    max_length_in=30,
    max_weight_lbs=15,
    icon='salmon_sockeye.png',
    value_lbc=3
)

salmon_chinook = FishSpecies(
    name = 'Chinook Salmon',
    max_length_in=60,
    max_weight_lbs=80,
    icon='salmon_chinook.png',
    value_lbc=5
)

class Fishing:
    def __init__(self, db):
        self.db = db

        # Add locations to activity!
        self.tributary_river = Location(
            db,
            id='tributary_river',
            name='Tributary River',
            drop_table=DropTable(
                drops = [
                    salmon_pink, 
                    salmon_coho, 
                    salmon_sockeye, 
                    salmon_chinook
                ],
                weights = [
                    50, # Common
                    30, # Uncommon
                    15, # Rare
                    5   # Epic
                ]
            )
        )

    @property
    def locations(self):
        l = []
        for id,object in vars(self).items():
            if isinstance(object, Location):
                l.append(object)
        return l
