# --------------------- Error Code Setup ---------------------

ERROR_DUPLICATE_USER = 0
ERROR_FAILED_AUTHENTICATION = 1
ERROR_FRIEND_ALREADY_FOUND = 2
ERROR_FRIEND_NOT_FOUND = 3
ERROR_USER_NOT_FOUND = 4

ERROR_MESSAGE = {
    ERROR_DUPLICATE_USER: "ERROR: found duplicate user.",
    ERROR_FAILED_AUTHENTICATION: "ERROR: authentication failed.",
    ERROR_FRIEND_ALREADY_FOUND: "ERROR: friendship already exists.",
    ERROR_FRIEND_NOT_FOUND: "ERROR: friendship does not exist.",
    ERROR_USER_NOT_FOUND: "ERROR: user does not exist in the social network."
}

def error_to_string(error_code: int) -> str:
    return ERROR_MESSAGE.get(error_code, "INVALID ERROR CODE")

# --------------------- Password Encryption ---------------------

import random

def generate_key() -> int:
    # Always generate the same key (used for consistent testing)
    random.seed(131)
    return random.randrange(1, 27)

def encrypt_password(password: str) -> str:
    # Shift each character by a fixed key
    encrypted = ""
    key = generate_key()
    for char in password:
        new_code = ord(char) + key
        if new_code > 126:
            new_code -= 94  # wrap around printable ASCII
        encrypted += chr(new_code)
    return encrypted

# --------------------- File and User Data Handling ---------------------

def string_to_user(string: str) -> tuple:
    # Parse a user string into a dictionary
    parts = string.strip().split('|')
    user_info = parts[0].split(',')
    friends = [f.strip() for f in parts[1].split(',')]

    name = user_info[0].strip()
    raw_password = user_info[1].strip()
    bio = ','.join(user_info[2:-1]).strip()
    country = user_info[-1].strip()
    
    return (name, {
        "password": encrypt_password(raw_password),
        "bio": bio,
        "country": country,
        "friends": friends
    })

def initialize_social_network_from_file(file_name: str) -> dict | int:
    # Read user data from file and build the network
    with open(file_name, "r") as file:
        lines = file.readlines()

    network = {}
    for line in lines:
        username, info = string_to_user(line)
        if username in network:
            return ERROR_DUPLICATE_USER
        network[username] = info

    return network

# --------------------- User Authentication ---------------------

def authenticate_user(user_name: str, password: str, network: dict) -> bool:
    # Check if username exists and password matches
    return (user_name in network and
            encrypt_password(password) == network[user_name]["password"])

# --------------------- Friend Operations ---------------------

def add_friend(user_name: str, password: str, friend_name: str, network: dict) -> None | int:
    if not authenticate_user(user_name, password, network):
        return ERROR_FAILED_AUTHENTICATION
    if friend_name not in network:
        return ERROR_USER_NOT_FOUND
    if friend_name == user_name:
        return None
    if friend_name in network[user_name]["friends"]:
        return ERROR_FRIEND_ALREADY_FOUND

    network[user_name]["friends"].append(friend_name)
    network[friend_name]["friends"].append(user_name)
    return None

def get_friend_index(user_name: str, friend_name: str, network: dict) -> int:
    # Find friend index in user's friend list
    try:
        return network[user_name]["friends"].index(friend_name)
    except ValueError:
        return -1

def remove_friend(user_name: str, password: str, friend_name: str, network: dict) -> None | int:
    if not authenticate_user(user_name, password, network):
        return ERROR_FAILED_AUTHENTICATION
    if friend_name not in network[user_name]["friends"]:
        return ERROR_FRIEND_NOT_FOUND

    network[user_name]["friends"].remove(friend_name)
    network[friend_name]["friends"].remove(user_name)
    return None

# --------------------- Friend Insights ---------------------

def num_countries_in_friends(user_name: str, password: str, network: dict) -> dict | int:
    if not authenticate_user(user_name, password, network):
        return ERROR_FAILED_AUTHENTICATION

    counts = {}
    for friend in network[user_name]["friends"]:
        country = network[friend]["country"]
        counts[country] = counts.get(country, 0) + 1

    return counts

def sort_friend_list(user_name: str, password: str, network: dict) -> int | None:
    if not authenticate_user(user_name, password, network):
        return ERROR_FAILED_AUTHENTICATION

    def common_friends(friend: str) -> int:
        return sum(1 for f in network[friend]["friends"] if f in network[user_name]["friends"])

    network[user_name]["friends"].sort(key=common_friends, reverse=True)
    return None

def get_level_friends(user_name: str, password: str, network: dict, degree: int) -> list | int:
    if not authenticate_user(user_name, password, network):
        return ERROR_FAILED_AUTHENTICATION
    if degree == 0:
        return [user_name]

    visited = {user_name: 0}
    queue = [(user_name, 0)]
    level_friends = []

    while queue:
        current, level = queue.pop(0)
        if level == degree and current != user_name:
            level_friends.append(current)
        elif level < degree:
            for friend in network[current]["friends"]:
                if friend not in visited:
                    visited[friend] = level + 1
                    queue.append((friend, level + 1))
    return level_friends

# --------------------- CLI Interface ---------------------

def social_network_application() -> None:
    user_file_path = input("Enter users file path: ")
    network = initialize_social_network_from_file(user_file_path)

    if isinstance(network, int):
        print(error_to_string(network))
        return

    print("Welcome to the Social Network!")

    while True:
        print("\nLogin")
        username = input("Username: ")
        password = input("Password: ")

        if not authenticate_user(username, password, network):
            print("Authentication failed.")
            continue

        print("Login successful.")
        while True:
            print("\nMenu Options:")
            print("1. Add Friend")
            print("2. Remove Friend")
            print("3. Display Friend List (Sorted)")
            print("4. Display nth Level Friends")
            print("5. Display countries in your network")
            print("6. Log Out")

            choice = input("Choose an option: ")

            if choice == '1':
                friend = input("Enter friend's username: ")
                result = add_friend(username, password, friend, network)
                if result is None:
                    sort_friend_list(username, password, network)
                    print("Friend added. Updated list:", network[username]["friends"])
                else:
                    print(error_to_string(result))
            elif choice == '2':
                friend = input("Enter friend's username: ")
                result = remove_friend(username, password, friend, network)
                if result is None:
                    sort_friend_list(username, password, network)
                    print("Friend removed. Updated list:", network[username]["friends"])
                else:
                    print(error_to_string(result))
            elif choice == '3':
                sort_friend_list(username, password, network)
                print("Sorted friends list:", network[username]["friends"])
            elif choice == '4':
                degree = int(input("Enter degree (1, 2, etc.): "))
                print("Friends at level", degree, ":", get_level_friends(username, password, network, degree))
            elif choice == '5':
                print("Friends by country:", num_countries_in_friends(username, password, network))
            elif choice == '6':
                print("Logged out.\n")
                break
            else:
                print("Invalid option. Try again.")

# --------------------- Main Function ---------------------

def main() -> None:
    social_network_application()

if __name__ == "__main__":
    main()
