from update_daily import run_update

# Refresh player data for both leagues without changing the daily player
if __name__ == "__main__":
    run_update(pick_daily=False)
