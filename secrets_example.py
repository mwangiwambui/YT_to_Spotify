import spotify_token as st
data = st.start_session("username", "password")
access_token = data[0]
expiration_date = data[1]
username = "username"