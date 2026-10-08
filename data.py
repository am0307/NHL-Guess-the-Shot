# Dictionary of NHL team abbreviations and their division/conference
TEAM_DIVISIONS_CONFERENCES = {"ANA": ("Pacific", "Western"), "BOS": ("Atlantic", "Eastern"), "BUF": ("Atlantic", "Eastern"),
                              "CGY": ("Pacific", "Western"), "CAR": ("Metro", "Eastern"), "CHI": ("Central", "Western"),
                              "COL": ("Central", "Western"), "CBJ": ("Metro", "Eastern"), "DAL": ("Central", "Western"),
                              "DET": ("Atlantic", "Eastern"), "EDM": ("Pacific", "Western"), "FLA": ("Atlantic", "Eastern"),
                              "LAK": ("Pacific", "Western"), "MIN": ("Central", "Western"), "MTL": ("Atlantic", "Eastern"),
                              "NSH": ("Central", "Western"), "NJD": ("Metro", "Eastern"), "NYI": ("Metro", "Eastern"),
                              "NYR": ("Metro", "Eastern"), "OTT": ("Atlantic", "Eastern"), "PHI": ("Metro", "Eastern"),
                              "PIT": ("Metro", "Eastern"), "SJS": ("Pacific", "Western"), "SEA": ("Pacific", "Western"),
                              "STL": ("Central", "Western"), "TBL": ("Atlantic", "Eastern"), "TOR": ("Atlantic", "Eastern"),
                              "UTA": ("Central", "Western"), "VAN": ("Pacific", "Western"), "VGK": ("Pacific", "Western"),
                              "WSH": ("Metro", "Eastern"), "WPG": ("Central", "Western")
                              }

# Players available to guess
PLAYER_IDS = {"Adam Fox":8479323, "Alex Ovechkin":8471214, "Auston Matthews":8479318, 
              "Cale Makar":8480069, "Cole Caufield":8481540, "Connor Bedard":8484144, 
              "Connor McDavid":8478402, "David Pastrnak":8477956, "Evan Bouchard":8480803, 
              "Filip Forsberg":8476887, "Jack Eichel":8478403, "Jack Hughes":8481559, 
              "Jason Robertson":8480027, "Kirill Kaprizov":8478864, "Kyle Connor":8478398, 
              "Leon Draisaitl":8477934, "Linus Ullmark":8476999, "Macklin Celebrini":8484801, 
              "Matthew Schaefer":8485366, "Matthew Tkachuk":8479314, "Matvei Michkov":8484387, 
              "Mitch Marner":8478483, "Nathan MacKinnon":8477492, "Nick Suzuki":8480018, 
              "Nikita Kucherov":8476453, "Patrick Kane":8474141, "Quinn Hughes":8480800, 
              "Rasmus Dahlin":8480839, "Robert Thomas":8480023, "Sebastian Aho":8478427, 
              "Sidney Crosby":8471675, "Tage Thompson":8479420, "Tim Stützle":8482116, 
              "William Nylander":8477939, "Zach Werenski":8478460
              }

# Video Sources
VIDEO_SOURCES = {"Adam Fox": {"URL":"https://youtu.be/VZdDy9x23Fo", "source":"Sportsnet"}, "Alex Ovechkin": {"URL":"https://youtu.be/rbdBRaVdPg4", "source":"the NHL"},
                 "Auston Matthews": {"URL":"https://youtu.be/vY5TIGmTFIA", "source":"Sportsnet"}, "Cale Makar": {"URL":"https://youtu.be/POu3KUZy_pk", "source":"Sportsnet"}, 
                 "Cole Caufield": {"URL":"https://youtu.be/XEFu3Q305gI", "source":"the NHL"}, "Connor Bedard": {"URL":"https://youtu.be/nYXS4imOm8g", "source":"Sportsnet"}, 
                 "Connor McDavid": {"URL":"https://youtu.be/m2uGGihNIMA", "source":"Sportsnet"}, "David Pastrnak": {"URL":"https://youtu.be/NABw97A-51k", "source":"the NHL"}, 
                 "Evan Bouchard": {"URL":"https://youtu.be/7EvbV7_CtWU", "source":"the NHL"}, "Filip Forsberg": {"URL":"https://youtu.be/CZDUm3rRhqc", "source":"Sportsnet"}, 
                 "Jack Eichel": {"URL":"https://youtu.be/VNYDKFxl-6w", "source":"Sportsnet"}, "Jack Hughes": {"URL":"https://youtu.be/VkQGhT2MAmc", "source":"Sportsnet"}, 
                 "Jason Robertson": {"URL":"https://youtu.be/nyJGb5kJKKc", "source":"Sportsnet"}, "Kirill Kaprizov": {"URL":"https://youtu.be/n-If3Dx62lQ", "source":"Sportsnet"}, 
                 "Kyle Connor": {"URL":"https://youtu.be/L5Yf06msrTQ", "source":"Sportsnet"}, "Leon Draisaitl": {"URL":"https://youtu.be/kEr5-t0RKwY", "source":"Sportsnet"}, 
                 "Linus Ullmark": {"URL":"https://youtu.be/B97Kxv7ji-o", "source":"the NHL"}, "Macklin Celebrini": {"URL":"https://youtu.be/Baz4HviPu0U", "source":"the NHL"}, 
                 "Matthew Schaefer": {"URL":"https://youtu.be/EBZvKMEq6Sw", "source":"Sportsnet"}, "Matthew Tkachuk": {"URL":"https://youtu.be/268pu91OSjI", "source":"Sportsnet"}, 
                 "Matvei Michkov": {"URL":"https://youtu.be/ub7BELV4w2k", "source":"Sportsnet"}, "Mitch Marner": {"URL":"https://youtu.be/Xz-S3j1SU1w", "source":"Sportsnet"}, 
                 "Nathan MacKinnon": {"URL":"https://youtu.be/b-7ogDQRrDs", "source":"Sportsnet"}, "Nick Suzuki": {"URL":"https://youtu.be/8Tu3x0j1OA4", "source":"Sportsnet"}, 
                 "Nikita Kucherov": {"URL":"https://youtu.be/Hajw4hWGjvg", "source":"the NHL"}, "Patrick Kane": {"URL":"https://youtu.be/qg5UrHpmjmY", "source":"Sportsnet"}, 
                 "Quinn Hughes": {"URL":"https://youtu.be/iXPFnh4wBBI", "source":"Sportsnet"}, "Rasmus Dahlin": {"URL":"https://youtu.be/EPXMne8YNsU", "source":"Sportsnet"}, 
                 "Robert Thomas": {"URL":"https://youtu.be/Xtsoaa9_TxQ", "source":"Sportsnet"}, "Sebastian Aho": {"URL":"https://youtu.be/VAFprF3TSXI", "source":"Sportsnet"}, 
                 "Sidney Crosby": {"URL":"https://youtu.be/tAh0LK1sstI", "source":"Sportsnet"}, "Tage Thompson": {"URL":"https://youtu.be/6dX8dRR86c0", "source":"Sportsnet"}, 
                 "Tim Stützle": {"URL":"https://youtu.be/WgVWQtj3x7w", "source":"the NHL"}, "William Nylander": {"URL":"https://youtu.be/NOt4rzyGwdY", "source":"the NHL"}, 
                 "Zach Werenski": {"URL":"https://youtu.be/mCfEyeCIgiY", "source":"Sportsnet"}
                 }