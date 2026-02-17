from environs import Env

env = Env()
env.read_env()

GOOGLE_SHEETS_CREDENTIALS = env.str("GOOGLE_CREDENTIALS_FILE")
SPREADSHEET_ID = env.str("GOOGLE_SHEET_ID")