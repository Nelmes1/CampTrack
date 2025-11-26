users = {
    'admin': [],
    'scout leader': [],
    'logistics coordinator': []
}


def disabled_logins(username):
    with open('disabled_logins.txt', 'a') as file:
        file.write(username + ',')


def check_disabled_logins(username):
    try:
        with open('disabled_logins.txt', 'r') as file:
            disabled = file.read()
            disabled_usernames = disabled.split(',')
            if username in disabled_usernames:
                return True
    except FileNotFoundError:
        return False
    return False


def enable_login(username):
    try:
        with open('disabled_logins.txt', 'r') as file:
            disabled = file.read()
            disabled_usernames = disabled.split(',')

            if username in disabled_usernames:
                disabled_usernames.remove(username)

                with open('disabled_logins.txt', 'w') as file:
                    if disabled_usernames:
                        file.write(','.join(disabled_usernames) + ',')
                    else:
                        file.write('')

                return True
    except FileNotFoundError:
        return False
    return False


def save_logins():
    with open('logins.txt', 'w') as file:
        for admin in users['admin']:
            file.write(f"admin,{admin['username']},{admin['password']}\n")
        for leader in users['scout leader']:
            file.write(f"scout leader,{leader['username']},{leader['password']}\n")
        for coordinator in users['logistics coordinator']:
            file.write(f"logistics coordinator,{coordinator['username']},{coordinator['password']}\n")


def load_logins():
    try:
        with open('logins.txt', 'r') as file:
            lines = file.readlines()
            users.clear()
            users.update({
                'admin': [],
                'scout leader': [],
                'logistics coordinator': []
            })
            for line in lines:
                line = line.strip()

                parts = [item.strip() for item in line.split(',')]
                if len(parts) < 3:
                    print(f"Skipping malformed line: {line}")
                    continue

                role, username, password = parts[:3]

                if role == 'admin':
                    users['admin'].append({'username': username, 'password': password})
                elif role == 'scout leader':
                    users['scout leader'].append({'username': username, 'password': password})
                elif role == 'logistics coordinator':
                    users['logistics coordinator'].append({'username': username, 'password': password})
            if not users['admin']:
                users['admin'].append({'username': 'admin', 'password': ''})

    except FileNotFoundError:
        print('\n logins.txt not found')
