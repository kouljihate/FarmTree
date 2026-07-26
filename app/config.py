TREE_KINDS = [
    "Cherry",
    "Prunes",
    "Nectarine",
    "Peach",
    "Citrus",
    "Figue"
]

# Variety mappings for each tree kind
TREE_VARIETIES = {
    "Cherry": [
        "Bing", "Rainier", "Lapins", "Stella", "Van", "Santina", "Sweetheart",
        "Skeena", "Regina", "Chelan", "Tieton", "Benton", "Index", "Brooks",
        "Tulare", "Coral Champagne", "Early Burlat", "Black Republican",
        "Royal Ann (Napoleon)", "Montmorency", "English Morello", "Balaton",
        "Danube", "Jubileum", "Kordia", "Samba", "Sandra Rose", "Summit",
        "Lambert", "Sam", "Utah Giant", "Kristin", "Emperor Francis",
        "Hedelfingen", "Schmidt", "Vandalay", "White Gold", "Other"
    ],
    "Prunes": [
        "Stanley", "Italian", "Early Italian", "French Petite", "Brooks",
        "Imperial Epineuse", "Green Gage", "Mirabelle de Metz",
        "Yellow Egg", "Blue Damson", "Shropshire Damson", "Farleigh Damson",
        "Prune Damson", "President", "Valor", "Vision", "Voyager",
        "Seneca", "Longjohn", "Moyer", "Tragedy", "Valor", "Verity",
        "Other"
    ],
    "Nectarine": [
        "Fantasia", "Flavortop", "Redgold", "Harflame", "Harblaze",
        "Arctic Rose", "Arctic Star", "Arctic Sweet", "Arctic Glo",
        "Arctic Jay", "Arctic Queen", "Arctic King", "Arctic Belle",
        "Arctic Pride", "Double Delight", "Goldmine", "Heavenly White",
        "Independence", "Karla Rose", "Lizzie", "Mericrest", "Nectar Babe",
        "Panamint", "Pink Diamond", "Ruby Diamond", "Sunglo", "Sunlite",
        "Sunred", "Surecrop", "Sweet Scarlett", "Venus", "Zephyr",
        "Other"
    ],
    "Peach": [
        "Redhaven", "Elberta", "Hale Haven", "J.H. Hale", "Contender",
        "Reliance", "Madison", "Cresthaven", "Encore", "Loring",
        "Coralstar", "Glohaven", "Suncrest", "Springcrest", "Garnet Beauty",
        "Early Redhaven", "Harson", "Harken", "Harbrite", "Veeglo",
        "Harrow Beauty", "Harrow Diamond", "Harrow Dawn", "Harrow Fair",
        "Harcrest", "Vollie", "Redskin", "Allstar", "Bounty", "Coralstar",
        "Glowingstar", "Blazingstar", "Risingstar", "Starfire", "Redstar",
        "Flamin Fury PF-1", "Flamin Fury PF-5B", "Flamin Fury PF-15A",
        "Flamin Fury PF-17", "Flamin Fury PF-23", "Flamin Fury PF-24",
        "Flamin Fury PF-25", "Flamin Fury PF-27A",
        "White Lady", "Blushingstar", "Snow King", "Snow Giant",
        "Arctic Supreme", "Babygold 5", "Babygold 7", "Veecling",
        "Vitall", "Virgil", "Venture", "Catherina", "Vulgold", "Vinegold",
        "Vulcan", "Other"
    ],
    "Citrus": [
        # Oranges
        "Navel Orange", "Valencia Orange", "Blood Orange", "Cara Cara Navel",
        "Hamlin Orange", "Pineapple Orange", "Seville Orange", "Bergamot Orange",
        "Temple Orange", "Ambersweet Orange", "Midsweet Orange", "Parson Brown",
        # Lemons
        "Eureka Lemon", "Lisbon Lemon", "Meyer Lemon", "Ponderosa Lemon",
        "Femminello Lemon", "Verna Lemon", "Variegated Pink Eureka Lemon",
        "Yen Ben Lemon", "Villafranca Lemon", "Santa Teresa Lemon",
        # Limes
        "Persian Lime", "Key Lime", "Kaffir Lime", "Bearss Lime",
        "Mexican Lime", "Finger Lime", "Rangpur Lime", "Sweet Lime",
        # Mandarins/Tangerines
        "Clementine", "Satsuma (Owari)", "Satsuma (Miho Wase)", "Satsuma (Okitsu Wase)",
        "Dancy Tangerine", "Honey Murcott", "Pixie Mandarin", "Tango Mandarin",
        "Kishu Mandarin", "Fairchild Mandarin", "Fallglo Mandarin",
        "Sunburst Mandarin", "Robinson Mandarin", "Orlando Mandarin",
        # Grapefruits
        "Ruby Red Grapefruit", "Star Ruby Grapefruit", "Flame Grapefruit",
        "Rio Red Grapefruit", "Marsh White Grapefruit", "Duncan Grapefruit",
        "Thompson Grapefruit", "Pink Grapefruit", "Oro Blanco",
        # Others
        "Buddha's Hand", "Calamondin", "Kumquat (Nagami)", "Kumquat (Meiwa)",
        "Etrog Citron", "Pummelo", "Yuzu", "Sudachi", "Kabosu",
        "Other"
    ],
    "Figue": [
        "Brown Turkey", "Black Mission", "Kadota", "Calimyrna", "Adriatic",
        "Celeste", "Chicago Hardy", "LSU Purple", "LSU Gold", "Tena",
        "Conadria", "Desert King", "Excel", "Flanders", "Ge Neri",
        "Green Ischia", "Hardy Chicago", "Improved Brown Turkey", "Ischia",
        "Jolly Tiger", "Kadota", "King", "Longue d'Aout", "Madeleine",
        "Marseilles", "Mary Lane", "Negronne", "Olympian", "Osborn Prolific",
        "Panachee (Tiger)", "Pastiliere", "Petite Negra", "Ronde de Bordeaux",
        "Sal's EL", "San Piero", "Smith", "Stella", "Sweet Joy",
        "Violette de Bordeaux", "White Genoa", "White Marseilles",
        "Yellow Long Neck", "Other"
    ]
}

TREE_STATUSES = [
    ("Healthy", "#2E7D32"),
    ("Needs Water", "#1565C0"),
    ("Needs Fertilizer", "#E65100"),
    ("Diseased", "#C62828"),
    ("Pest Infestation", "#AD1457"),
    ("Pruned", "#6A1B9A"),
    ("Damaged", "#BF360C"),
    ("Dead", "#455A64"),
    ("Flowering", "#C2185B"),
    ("Fruiting", "#F57F17"),
    ("New Planting", "#558B2F"),
]

STATUS_LOOKUP = {label: color for label, color in TREE_STATUSES}