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
        self.relative_size = self._relative_size()
        self.weight_lbs = self._weight()
        self.length_in = self._length()

    def _relative_size(self):
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
            id,
            name,
            max_weight_lbs,
            max_length_in,
            icon,
            value_lbc
        ):
        self.id = id
        self.name = name
        self.max_weight_lbs = max_weight_lbs
        self.max_length_in = max_length_in
        self.icon = icon
        self.value_lbc = value_lbc

# Tributary River

salmon_pink = FishSpecies(
    id = 'salmon_pink',
    name = 'Pink Salmon',
    max_weight_lbs=15,
    max_length_in=30,
    icon='salmon_pink.png',
    value_lbc = 1
)

salmon_coho = FishSpecies(
    id = 'salmon_coho',
    name = 'Coho Salmon',
    max_length_in=42,
    max_weight_lbs=36,
    icon='salmon_coho.png',
    value_lbc=2
)

salmon_sockeye = FishSpecies(
    id = 'salmon_sockeye',
    name = 'Sockeye Salmon',
    max_length_in=30,
    max_weight_lbs=15,
    icon='salmon_sockeye.png',
    value_lbc=3
)

salmon_chinook = FishSpecies(
    id = 'salmon_chinook',
    name = 'Chinook Salmon',
    max_length_in=60,
    max_weight_lbs=80,
    icon='salmon_chinook.png',
    value_lbc=5
)

# Open Ocean

arctic_grayling = FishSpecies(
    id = 'arctic_grayling',
    name = 'Arctic Grayling',
    max_length_in=30,
    max_weight_lbs=8,
    icon='arctic_grayling.png',
    value_lbc=1
)

arctic_cod = FishSpecies(
    id = 'arctic_cod',
    name = 'Arctic Cod',
    max_length_in=16,
    max_weight_lbs=36,
    icon='arctic_cod.png',
    value_lbc=1
)

alaska_rockfish = FishSpecies(
    id = 'alaska_rockfish',
    name = 'Alaska Rockfish',
    max_length_in=27,
    max_weight_lbs=11,
    icon='alaska_rockfish.png',
    value_lbc=3
)

pacific_halibut = FishSpecies(
    id = 'pacific_halibut',
    name = 'Pacific Halibut',
    max_weight_lbs=500,
    max_length_in=96,
    icon='pacific_halibut.png',
    value_lbc = 3
)

bluefin_tuna = FishSpecies(
    id = 'bluefin_tuna',
    name = 'Bluefin Tuna',
    max_length_in=100,
    max_weight_lbs=500,
    icon='bluefin_tuna.png',
    value_lbc=5
)

swordfish = FishSpecies(
    id = 'swordfish',
    name = 'Swordfish',
    max_weight_lbs=1400,
    max_length_in=168,
    icon='swordfish.png',
    value_lbc = 6
)

# Estuary

scup = FishSpecies(
    id = 'scup',
    name = 'Scup',
    max_weight_lbs=4,
    max_length_in=18,
    icon='scup.png',
    value_lbc = 1
)

menhaden = FishSpecies(
    id = 'menhaden',
    name = 'Menhaden',
    max_weight_lbs=1,
    max_length_in=15,
    icon='menhaden.png',
    value_lbc = 1
)

striped_bass = FishSpecies(
    id = 'striped_bass',
    name = 'Striped Bass',
    max_weight_lbs=40,
    max_length_in=35,
    icon='striped_bass.png',
    value_lbc = 3
)

black_sea_bass = FishSpecies(
    id = 'black_sea_bass',
    name = 'Black Sea Bass',
    max_weight_lbs=9,
    max_length_in=26,
    icon='black_sea_bass.png',
    value_lbc = 3
)

bonito = FishSpecies(
    id = 'bonito',
    name = 'Bonito',
    max_weight_lbs=18,
    max_length_in=30,
    icon='bonito.png',
    value_lbc = 3
)

bluefish = FishSpecies(
    id = 'bluefish',
    name = 'Bluefish',
    max_weight_lbs=31,
    max_length_in=39,
    icon='bluefish.png',
    value_lbc = 5
)

# Coral Reef

sergeant_major = FishSpecies(
    id = 'sergeant_major',
    name = 'Sergeant Major',
    max_weight_lbs=0.5,
    max_length_in=9,
    icon='sergeant_major.png',
    value_lbc = 1
)

yellowtail_snapper = FishSpecies(
    id = 'yellowtail_snapper',
    name = 'Yellowtail Snapper',
    max_weight_lbs=11,
    max_length_in=24,
    icon='yellowtail_snapper.png',
    value_lbc = 1
)

spanish_mackerel = FishSpecies(
    id = 'spanish_mackerel',
    name = 'Spanish Mackerel',
    max_weight_lbs=14,
    max_length_in=37,
    icon='spanish_mackerel.png',
    value_lbc = 2
)

goatfish = FishSpecies(
    id = 'goatfish',
    name = 'Goatfish',
    max_weight_lbs=2.5,
    max_length_in=15,
    icon='goatfish.png',
    value_lbc = 2
)

parrotfish = FishSpecies(
    id = 'parrotfish',
    name = 'Parrotfish',
    max_weight_lbs=3.5,
    max_length_in=25,
    icon='parrotfish.png',
    value_lbc = 3
)

hogfish = FishSpecies(
    id = 'hogfish',
    name = 'Hogfish',
    max_weight_lbs=34,
    max_length_in=35,
    icon='hogfish.png',
    value_lbc = 3
)

mahi_mahi = FishSpecies(
    id = 'mahi_mahi',
    name = 'Mahi Mahi',
    max_weight_lbs=40,
    max_length_in=40,
    icon='mahi_mahi.png',
    value_lbc = 4
)

red_grouper = FishSpecies(
    id = 'red_grouper',
    name = 'Red Grouper',
    max_weight_lbs=51,
    max_length_in=49,
    icon='red_grouper.png',
    value_lbc = 4
)

trevally = FishSpecies(
    id = 'trevally',
    name = 'Giant trevally',
    max_weight_lbs=175,
    max_length_in=67,
    icon='trevally.png',
    value_lbc = 5
)

humphead_wrasse = FishSpecies(
    id = 'humphead_wrasse',
    name = 'Humphead Wrasse',
    max_weight_lbs=400,
    max_length_in=80,
    icon='humphead_wrasse.png',
    value_lbc = 6
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

        self.open_ocean = Location(
            db,
            id='open_ocean',
            name='Open Ocean',
            drop_table=DropTable(
                drops = [
                    arctic_grayling, 
                    arctic_cod, 
                    alaska_rockfish, 
                    pacific_halibut,
                    bluefin_tuna,
                    swordfish
                ],
                weights = [
                    30, # Uncommon
                    30, # Uncommon
                    15, # Rare
                    15, # Rare
                    5,  # Epic
                    1   # Epic
                ]
            )
        )

        self.estuary = Location(
            db,
            id='estuary',
            name='Estuary',
            drop_table=DropTable(
                drops = [
                    scup, 
                    menhaden, 
                    striped_bass, 
                    black_sea_bass, 
                    bonito, 
                    bluefish
                ],
                weights = [
                    25, # Uncommon
                    25, # Uncommon
                    15, # Rare
                    15, # Rare
                    15, # Rare
                    1   # Epic
                ]
            )
        )

        self.coral_reef = Location(
            db,
            id='coral_reef',
            name='Coral Reef',
            drop_table=DropTable(
                drops = [
                    sergeant_major,
                    yellowtail_snapper,
                    spanish_mackerel,
                    goatfish,
                    parrotfish,
                    hogfish,
                    mahi_mahi,
                    red_grouper,
                    trevally,
                    humphead_wrasse
                ],
                weights = [
                    20,
                    20,
                    15, 
                    15, 
                    10, 
                    10,
                    4, 
                    3,
                    2, 
                    1
                ]
            )
        )

    @property
    def fishing_attempts_allowed(self):
        return len(self.locations)

    @property
    def locations(self):
        l = []
        for id,object in vars(self).items():
            if isinstance(object, Location):
                l.append(object)
        return l

    @property
    def species(self):
        s = {}
        for location in self.locations:
            for species in location.species:
                s[species.id] = species
                setattr(s[species.id], 'location', location)

        return s
