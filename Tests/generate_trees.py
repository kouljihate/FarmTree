import sqlite3
import random
import requests
import csv
from io import StringIO

DB_PATH = "../farm_tree_manager.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT NOT NULL,
            age INTEGER,
            health TEXT
        )
    """)
    conn.commit()
    conn.close()

def fetch_tree_species(limit=1000):
    # Download GlobalTreeSearch CSV (example link)
    url = "https://tools.bgci.org/global_tree_search.php/download"  
    response = requests.get(url)
    response.raise_for_status()

    # Parse CSV
    csv_file = StringIO(response.text)
    reader = csv.reader(csv_file)
    species_list = [row[0] for row in reader if row]  # species names in first column

    # Pick random 1000 species
    return random.sample(species_list, limit)

def generate_trees():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    health_options = ["Healthy", "Needs Water", "Diseased"]

    for species in fetch_tree_species():
        age = random.randint(1, 100)  # random age
        health = random.choice(health_options)
        cursor.execute("INSERT INTO trees (species, age, health) VALUES (?, ?, ?)",
                       (species, age, health))

    conn.commit()
    conn.close()
    print("✅ 1000 trees generated and saved to database.")

if __name__ == "__main__":
    generate_trees()
