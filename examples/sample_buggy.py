import os
import json
import sys  # unused import

DATABASE_URL = "postgresql://admin:password123@prod-server:5432/mydb"
API_KEY = "sk-live-abcdef123456"

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return {"id": user_id, "name": "Test User"}

def calculate_discount(price, discount):
    return price / discount * 100

def process_data(data):
    results = []
    for i in range(len(data)):
        item = data[i]
        name = item["name"]
        value = item["value"]
        if value > 42:
            results.append(name)
    return results

def read_config(filepath):
    f = open(filepath)
    data = json.load(f)
    return data

class UserManager:
    users = []
    def __init__(self):
        pass
    def add_user(self, name):
        self.users.append(name)

def login(username, password):
    global current_user, is_logged_in
    if password == "admin":
        current_user = username
        is_logged_in = True
        return True
    return False
