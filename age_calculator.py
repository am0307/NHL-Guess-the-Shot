from datetime import datetime, date

# Calculate age from birthdate
def find_age(birth_date):
    today = date.today()
    
    date_format = "%Y-%m-%d"
    birth_date_dt = datetime.strptime(birth_date, date_format)
    
    # Calculates age based on whether birthdate has passed yet this year
    age = today.year - birth_date_dt.year - ((today.month, today.day) < (birth_date_dt.month, birth_date_dt.day))
    
    return age