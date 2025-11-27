from user_logins import load_logins
from login_auth import login_loop

print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
print('\nWelcome to CampTrack! Please select a user.')

load_logins()
login_loop()
