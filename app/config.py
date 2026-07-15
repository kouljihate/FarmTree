TREE_KINDS = [
    "Oak", "Pine", "Maple", "Birch", "Cedar", "Spruce", "Fir", "Willow", "Elm", "Ash",
    "Beech", "Chestnut", "Hickory", "Walnut", "Poplar", "Cottonwood", "Sycamore", "Magnolia",
    "Dogwood", "Redwood", "Sequoia", "Cypress", "Juniper", "Yew", "Hemlock", "Larch",
    "Tamarack", "Bald Cypress", "Ginkgo", "Dawn Redwood", "Monkey Puzzle", "Wollemi Pine",
    "Baobab", "Acacia", "Eucalyptus", "Teak", "Mahogany", "Rosewood", "Ebony", "Sandalwood",
    "Olive", "Fig", "Date Palm", "Coconut Palm", "Royal Palm", "Date Palm", "Fan Palm",
    "Sago Palm", "Bamboo", "Banana", "Papaya", "Mango", "Avocado", "Citrus", "Apple", "Pear",
    "Cherry", "Plum", "Peach", "Apricot", "Nectarine", "Almond", "Walnut", "Pecan", "Pistachio",
    "Other"
]

TREE_STATUSES = [
    (1, "Healthy", "#2E7D32"),
    (2, "Needs Water", "#1565C0"),
    (3, "Needs Fertilizer", "#E65100"),
    (4, "Diseased", "#C62828"),
    (5, "Pest Infestation", "#AD1457"),
    (6, "Pruned", "#6A1B9A"),
    (7, "Damaged", "#BF360C"),
    (8, "Dead", "#455A64"),
    (9, "Flowering", "#C2185B"),
    (10, "Fruiting", "#F57F17"),
    (11, "New Planting", "#558B2F"),
]

STATUS_LOOKUP = {label: (id_, label, color) for id_, label, color in TREE_STATUSES}