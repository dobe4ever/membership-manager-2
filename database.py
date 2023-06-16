from sqlalchemy import create_engine, text
import os

db = os.environ['DB_CONNECTION_STRING']

engine = create_engine(db, connect_args={
  "ssl": {
    "ssl_ca": "/etc/ssl/cert.pem"
  }
})

# Add new user to the db or update personal info if it changed
def add_or_update_user(update):
    user = update.effective_user
    user_id = user.id
    username = user.username
    public_name = user.first_name 

    # Update user information in the database
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id})
        if user_data := result.fetchone():
            # User exists, update username and public name if different
            if user_data.username != username or user_data.public_name != public_name:
                conn.execute(
                    text("UPDATE users SET username = :username, public_name = :public_name WHERE user_id = :user_id"),
                    {'username': username, 'public_name': public_name, 'user_id': user_id}
                )
        else:
            # User doesn't exist, insert new row
            conn.execute(
                text("INSERT INTO users (user_id, username, public_name, active) VALUES (:user_id, :username, :public_name, 0)"),
                {'user_id': user_id, 'username': username, 'public_name': public_name}
            )

        # Print the first row from the users table
        result = conn.execute(text("SELECT * FROM users LIMIT 1"))
        print(result.fetchone())


# Lock and return address   
def get_address(coin, user_id, amount):
    with engine.connect() as conn:
        # Find an available address for the specified coin and user
        result = conn.execute(
            text("SELECT address FROM addresses WHERE type = :coin AND inUse = 'no'"),
            {'coin': coin}
        )
        row = result.fetchone()
        if row is None:
            return None
        address = row[0]

        # Update the address to inUse='yes', associate it with the user, and set the amount
        conn.execute(
            text("UPDATE addresses SET inUse = 'yes', userid = :user_id, amount = :amount WHERE address = :address"),
            {'user_id': user_id, 'amount': amount, 'address': address}
        )

        # Commit the changes to the database
        conn.commit()

        return address


def release_address(user_id):
    with engine.connect() as conn:
        # Find the address associated with the user
        result = conn.execute(
            text("SELECT address FROM addresses WHERE userid = :user_id"),
            {'user_id': user_id}
        )
        row = result.fetchone()
        if row is not None:
            address = row[0]

            # Reset the address to inUse='no', clear the associated user ID, and set the amount to 0.0
            conn.execute(
                text("UPDATE addresses SET inUse = 'no', userid = 0, amount = 0.0 WHERE address = :address"),
                {'address': address}
            )

            # Commit the changes to the database
            conn.commit()


def transaction_in_progress(user_id):
    with engine.connect() as conn:
        # Check if there is an active transaction for the user
        result = conn.execute(
            text("SELECT COUNT(*) FROM addresses WHERE userid = :user_id AND inUse = 'yes'"),
            {'user_id': user_id}
        )
        count = result.fetchone()[0]

        if count <= 0:
            # No active transaction for the user
            return None
        
        # There is an active transaction for the user
        result = conn.execute(
            text("SELECT amount, type, address FROM addresses WHERE userid = :user_id AND inUse = 'yes'"),
            {'user_id': user_id}
        )
        row = result.fetchone()
        return row[0], row[1], row[2]


def get_user_membership(user_id):
    # Code to connect to the database and retrieve the user's active status and dates
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT active, signup_date, expiration_date FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        if not (user_data := result.fetchone()):
            return False, None, None
        active = bool(user_data.active)
        return active, user_data.signup_date, user_data.expiration_date


def new_member(update, context):
    # Extract new member information
    user = update.message.new_chat_members[0]

    # Pass the update object to add_or_update_user()
    add_or_update_user(update)

from telegram.error import BadRequest
from datetime import date
import datetime


def kick_expired_members(bot, group_id):
    print("Executing kick_expired_members function")
    with engine.connect() as conn:
        # Update 'active' field for expired members
        conn.execute(text("UPDATE users SET active = 0 WHERE active = 1 AND expiration_date < :today"), {'today': date.today()})

        # Fetch the IDs of expired members
        result = conn.execute(text("SELECT user_id FROM users WHERE active = 0"))
        expired_member_ids = [row[0] for row in result]  # Access the first column of each row

        print("Expired Member IDs:", expired_member_ids)

        # Ban the expired members from the group
        for user_id in expired_member_ids:
            try:
                bot.ban_chat_member(chat_id=group_id, user_id=user_id)
                print(f"Successfully banned user: {user_id}")
            except BadRequest as e:
                print(f"Failed to ban user {user_id}: {e}")

def job(bot, group_id):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Job executed at: {current_time}")
    kick_expired_members(bot, group_id)