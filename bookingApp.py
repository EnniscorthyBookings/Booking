import streamlit as st
import datetime
import csv
from datetime import timedelta
import random 
import pandas as pd
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pytz import timezone 
import pytz
from github import Github #####
from streamlit_js_eval import streamlit_js_eval
import calendar

    
# Set the timezone to "Europe/Dublin" (Ireland Time)
ireland_tz = pytz.timezone('Europe/Dublin')

# Get the current time in Ireland Time
current_time_ireland = datetime.datetime.now(ireland_tz)
ctif = current_time_ireland.strftime("%d-%m-%y %H:%M:%S")

g = Github(st.secrets["git"]["token"])
repo = g.get_repo('ohmydaysOMD/test')

# Define file paths for storing booking data
booking_data_file = "ohmydaysOMD/test/booking_data.csv"
# Load existing booking data from the CSV file
try:
    # Get the contents of the CSV file
    contents = repo.get_contents(booking_data_file)

    # Decode and read the content of the file
    csv_content = contents.decoded_content.decode('utf-8').splitlines()

    # Parse CSV content using csv.DictReader
    reader = csv.DictReader(csv_content)

    booking_data = {"room_bookings": {}, "room_availability": {}}

    # Iterate through rows in the CSV file
    for row in reader:
        booking_id = float(row["booking_id"])
        booking_data["room_bookings"][booking_id] = {
            "booking_id": booking_id,
            "date": row["date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "room": row["room"],
            "name": row["name"],
            "email": row["email"],
            "description": row["description"],
        }

        # Update room availability data
        if row["date"] not in booking_data["room_availability"]:
            booking_data["room_availability"][row["date"]] = {}
        if row["room"] not in booking_data["room_availability"][row["date"]]:
            booking_data["room_availability"][row["date"]][row["room"]] = []
        booking_data["room_availability"][row["date"]][row["room"]].append(
            (row["start_time"], row["end_time"])
        )

except FileNotFoundError:
    booking_data = {"room_bookings": {}, "room_availability": {}}

# Utility Functions
def is_valid_time(time_str):
    try:
        datetime.datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def is_room_available(date, start_time, end_time, room):
    if date not in booking_data["room_availability"]:
        return True

    if room not in booking_data["room_availability"][date]:
        return True

    for booking in booking_data["room_availability"][date][room]:
        b_start_time, b_end_time = booking
        if not (end_time <= b_start_time or start_time >= b_end_time):
            return False

    return True

# Generate a random 4-digit booking ID
# def generate_random_booking_id():
#     return random.randint(1000, 9999)

def generate_random_booking_id():
    now = datetime.datetime.now()
    unique_number = "{:02d}{:02d}{:02d}{:02d}{:02d}".format(
        now.year % 100, now.month, now.day, now.hour, now.minute
    )
    return float(unique_number)
    
# Book a Room
# Define a dictionary that maps room names to their capacities
room_capacity = {
    "Meeting Room 1": 14,
    "Desk 1": 1,
    "Desk 2": 1,
    "Desk 3": 1,
    "Desk 4": 1,
}



def book_room():
    st.header("Book a Room or a Desk")
    date = st.date_input("Select the Date:", min_value=current_time_ireland.date(), value=None, format="DD/MM/YYYY")
    current_date = current_time_ireland.date()
    if date:
        office_start_time = datetime.time(8, 0)
        office_end_time = datetime.time(20, 0)
        start_times = [office_start_time]
        while start_times[-1] < office_end_time:
            next_time = (datetime.datetime.combine(date, start_times[-1]) + timedelta(minutes=15)).time()
            start_times.append(next_time)
        
        start_time = st.selectbox("Select the Start Time:", start_times, index=None)
        current_time = current_time_ireland.time()
        if start_time:
            if (date == current_date and start_time < current_time):
                st.warning("Start time should be from current date and time.")
            else:
                end_of_day = min(office_end_time, datetime.time(23, 59))
                available_end_times = [datetime.datetime.combine(date, start_time) + timedelta(minutes=i) for i in range(15, (end_of_day.hour - start_time.hour) * 60 + 1, 15)]
                formatted_end_times = [et.strftime('%H:%M:%S') for et in available_end_times]
                end_time = st.selectbox("Select the End Time:", formatted_end_times, index=None)
                if end_time:
                    repeat_booking = st.toggle("Repeat Booking")
                    if repeat_booking:
                        repeat_frequency = st.selectbox("Select Repeat Frequency:", ["Weekly", "Bi-Weekly", "Monthly"])
                    else:
                        repeat_frequency = None

                    available_room_options = []
                    for room, capacity in room_capacity.items():
                        if is_room_available(str(date), str(start_time), str(end_time), room):
                            available_room_options.append(f"{room} (Capacity: {capacity})")
                    
                    if not available_room_options:
                        st.warning("Rooms are not available during this time.")
                    else:
                        st.info("Available Rooms")
                        room_choice = st.selectbox("Select a Room:", available_room_options, index=None)
                        if room_choice:
                            st.subheader('Enter Booking Details')
                            if "Desk" in room_choice:
                                # Extract the selected room name (excluding the capacity information)
                                selected_room = room_choice.split(" (Capacity: ")[0]
                                description = "Desk Booking" #st.text_input("Enter Meeting Title:")
                                name = st.text_input("Enter your Name:")
                                email = st.text_input("Enter your Email:")
                                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                                    st.warning("Please enter a valid email address.")
                                    return
                            else:
                                # Extract the selected room name (excluding the capacity information)
                                selected_room = room_choice.split(" (Capacity: ")[0]
                                description = st.text_input("Enter Meeting Title:")
                                name = st.text_input("Enter your Name:")
                                email = st.text_input("Enter your Email:")
                                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                                    st.warning("Please enter a valid email address.")
                                    return
                            
                            if not name or not description:
                                st.warning("All details are mandatory.")
                            else:
                                if st.button("Book Room"):
                                    booking_id = generate_random_booking_id()  # Generate a random 4-digit booking ID
                                    booking_data["room_bookings"][booking_id] = {
                                        "booking_id": booking_id,
                                        "date": str(date),
                                        "start_time": str(start_time),
                                        "end_time": str(end_time),
                                        "room": selected_room,
                                        "name": name,
                                        "email": email,
                                        "description": description,
                                    }
                                    
                                     # Update CSV file on GitHub
                                    content = ""
                                    
                                    fieldnames = [
                                        "booking_id",
                                        "date",
                                        "start_time",
                                        "end_time",
                                        "room",
                                        "name",
                                        "email",
                                        "description",
                                    ]
                                    content += ','.join(fieldnames) + '\n'
                                    #contentFieldnames = content
                                    for booking_id, booking_info in booking_data["room_bookings"].items():
                                        content += ','.join([str(booking_id), booking_info["date"], booking_info["start_time"], booking_info["end_time"],
                                                             booking_info["room"], booking_info["name"], booking_info["email"], booking_info["description"]]) + '\n'


                                    # Delete the file
                                    #repo.create_file("ohmydaysOMD/test/booking_data.csv", "Booking Data Updated", content, branch="main")
                                    file = repo.get_contents("ohmydaysOMD/test/booking_data.csv", ref="main")
                                    path = "ohmydaysOMD/test"


                                    # Push updated CSV to GitHub repository
                                    repo.update_file(file.path, "Booking Data Updated", content, file.sha, branch="main")


                                    if repeat_booking:
                                        repeat_bookings(booking_id, date, start_time, end_time, selected_room, description, name, email, repeat_frequency)

                                        # Send confirmation email
                                        if send_confirmation_email(email, booking_id, name, description, selected_room, start_time.strftime('%H:%M:%S'), end_time):
                                            st.success(f"Booking successful! Your booking ID is {booking_id}.")
                                            st.success("A confirmation email has been sent to the registered mail.")
                                        else:
                                            st.success(f"Booking successful! Your booking ID is {booking_id}.")
                                            st.warning("But confirmation email could not be sent to the registered mail.")
                                    else:
                                        # Send confirmation email
                                        if send_confirmation_email(email, booking_id, name, description, selected_room, start_time.strftime('%H:%M:%S'), end_time):
                                            st.success(f"Booking successful! Your booking ID is {booking_id}.")
                                            st.success("A confirmation email has been sent to the registered mail.")
                                        else:
                                            st.success(f"Booking successful! Your booking ID is {booking_id}.")
                                            st.warning("But confirmation email could not be sent to the registered mail.")

                                    
def repeat_bookings(original_booking_id, date, start_time, end_time, room, description, name, email, repeat_frequency):
    booking_data = {"room_bookings": {}}
    
    if repeat_frequency == "Weekly":
        interval = 7
        freqInt = 52
    elif repeat_frequency == "Bi-Weekly":
        interval = 14
        freqInt = 26
    elif repeat_frequency == "Monthly":
        interval = 28
        freqInt = 12

    bookings_to_write = []  # List to store booking data to write to CSV

    for i in range(freqInt):  # Repeat for the specified frequency
        new_date = date + timedelta(days=i * interval)
        new_booking_id = original_booking_id + i * 0.1
        booking_data["room_bookings"][new_booking_id] = {
            "booking_id": new_booking_id,
            "date": str(new_date.strftime('%Y-%m-%d')),
            "start_time": str(start_time),
            "end_time": str(end_time),
            "room": room,
            "name": name,
            "email": email,
            "description": description,
        }
        
        # Append booking info to the list
        bookings_to_write.append([
            str(new_booking_id),
            str(new_date.strftime('%Y-%m-%d')),
            str(start_time),
            str(end_time),
            room,
            name,
            email,
            description
        ])
    
    # Save the repeated booking data to the CSV file
    update_booking_csv(bookings_to_write)


def is_upcoming(booking, current_datetime):
    date_str = booking["date"]
    time_str = booking["start_time"]
    
    try:
        booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        booking_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
        booking_datetime = datetime.datetime.combine(booking_date, booking_time)
        current_datetime = datetime.datetime.strptime(current_datetime, '%d-%m-%y %H:%M:%S')
        
        return booking_datetime > current_datetime
    except ValueError:
        st.warning(f"Invalid date or time format found: {date_str} {time_str}. Skipping this booking.")
        return False


def cancel_room():
    st.header("Cancel Room Reservation")
    
    # Get the list of booked rooms
    booked_rooms = list(booking_data["room_bookings"].values())

    if not booked_rooms:
        st.warning("There are no existing room reservations to cancel.")
        return

    # Filter the reservations to include only upcoming bookings
    current_datetime = ctif
    upcoming_reservations = [booking for booking in booked_rooms if is_upcoming(booking, current_datetime)]

    if not upcoming_reservations:
        st.warning("No upcoming bookings to cancel.")
        return

    st.subheader("Select the reservation to cancel:")
    selected_reservation = st.selectbox("Upcoming Reservations", [f"Booking ID {booking_id}" for booking_id in booking_data["room_bookings"].keys() if is_upcoming(booking_data["room_bookings"][booking_id], current_datetime)], index=None)

    if selected_reservation:
        user_email_to_cancel = st.text_input("Enter Registered Mail used for booking:")

        if user_email_to_cancel:
            user_email_to_cancel = user_email_to_cancel.lower()
            if st.button("Cancel Reservation"):
                selected_booking_id = float(selected_reservation.split()[-1].strip())

                if selected_booking_id in booking_data["room_bookings"]:
                    reservation = booking_data["room_bookings"][selected_booking_id]
                    room = reservation["room"]
                    date = reservation["date"]
                    start_time = reservation["start_time"]
                    end_time = reservation["end_time"]
                    name = reservation["name"]  # Retrieve name from reservation data
                    email = reservation["email"]  # Retrieve email from reservation data
                    description = reservation["description"]  # Retrieve description from reservation data

                    formatted_start_time = str(start_time)
                    formatted_end_time = str(end_time)
                    room_availability = booking_data["room_availability"]

                    if date in room_availability and room in room_availability[date]:
                        room_availability[date][room] = [
                            booking
                            for booking in room_availability[date][room]
                            if (formatted_start_time, formatted_end_time)
                            != (booking[0], booking[1])
                        ]

                    if user_email_to_cancel == reservation["email"].lower():
                        booking_data["room_bookings"].pop(selected_booking_id)

                        # Update CSV file
                        update_booking_csv()

                        # Update room availability
                        if str(date) not in booking_data["room_availability"]:
                            booking_data["room_availability"][str(date)] = {}
        
                        user_email = reservation["email"]
                        if send_cancellation_email(user_email,selected_booking_id, reservation['name'],reservation['description'],date,room,start_time,end_time):
                            st.success(f"Reservation (Booking ID {selected_booking_id}) has been cancelled.")
                            st.success("A confirmation email has been sent to the registered email.")
                        else:
                            st.success(f"Reservation (Booking ID {selected_booking_id}) has been cancelled.")
                            st.warning("But confirmation email could not be sent to the registered email.")
                    else:
                        st.warning("Email address does not match. Cancellation failed.")

def update_booking_csv(bookings_df):
    # Write DataFrame to CSV file
    bookings_df.to_csv(booking_data_file, index=False)
    
    # Read updated content from the CSV file
    with open(booking_data_file, "r") as file:
        content = file.read()
    
    # Update CSV file on GitHub
    file = repo.get_contents("ohmydaysOMD/test/booking_data.csv", ref="main")
    repo.update_file(file.path, "Booking Data Updated", content, file.sha, branch="main")

def send_cancellation_email(user_email,booking_id,name,description,date1,selected_room,start_time,end_time):
    # Your email credentials
    sender_email = st.secrets["sender"]["email"]
    sender_password = st.secrets["sender"]["password"]

    # Create the email content
    message = MIMEMultipart()
    message["From"] = 'HSE Booking System'
    message["To"] = user_email
    message["Subject"] = f"Cancellation Confirmation: (ID-{booking_id})"

    # Message body
    #message_text = f"Hello {name}!\n\nWe're sorry to inform you that your booking has been canceled. Here are the details of the canceled reservation:\n\n{booking_details}\n\nIf you have any questions or need further assistance, please don't hesitate to contact us.\n\nBest regards,\nYour Meeting Room Booking Team"
    # Create the email content as an HTML table
    message_text = f"""
<html>
<body>
    <p>Hello {name}!</p>
    <p>We're sorry to inform you that your booking has been canceled. Here are the details of the canceled reservation:</p>
    <table style="width: 100%;">
        <tr>
            <td><strong>Booking ID:</strong></td>
            <td>{booking_id}</td>
        </tr>
        <tr>
            <td><strong>Meeting Title:</strong></td>
            <td>{description}</td>
        </tr>
        <tr>
            <td><strong>Date:</strong></td>
            <td>{date1}</td>
        </tr>
        <tr>
            <td><strong>Location:</strong></td>
            <td>{selected_room}</td>
        </tr>
        <tr>
            <td><strong>Start Time:</strong></td>
            <td>{start_time}</td>
        </tr>
        <tr>
            <td><strong>End Time:</strong></td>
            <td>{end_time}</td>
        </tr>
    </table>
    <p>If you have any questions or need further assistance, please don't hesitate to contact us.</p>
    <p>Best regards,<br>Your Meeting Room Booking Team</p>
</body>
</html>
"""

    message.attach(MIMEText(message_text, "html"))

    # Connect to the SMTP server
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Replace with your SMTP server and port
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, user_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email not sent. Error: {str(e)}")
        return False


def view_reservations():
    st.header("View Bookings")

    # Get the list of booked rooms
    booked_rooms = list(booking_data["room_bookings"].values())

    if not booked_rooms:
        st.warning("There are no existing room reservations to view.")
        return

    # Get the current date and time
    current_datetime = datetime.datetime.strptime(ctif, '%d-%m-%y %H:%M:%S')
    # Create separate lists for past and upcoming bookings
    past_bookings = []
    upcoming_bookings = []

    for booking in booked_rooms:
        date_str = booking["date"]
        time_str = booking["start_time"]
        
        try:
            # Parse the date string in the format yyyy-mm-dd
            booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
            booking_datetime = datetime.datetime.combine(booking_date, booking_time)
            
            if booking_datetime < current_datetime:
                past_bookings.append(booking)
            else:
                upcoming_bookings.append(booking)
        except ValueError:
            st.warning(f"Invalid date format found: {date_str}. Skipping this booking.")

    # Sort the bookings by date and time
    past_bookings = sorted(past_bookings, key=lambda x: (x["date"], x["start_time"]))
    upcoming_bookings = sorted(upcoming_bookings, key=lambda x: (x["date"], x["start_time"]))

    tab1, tab2 = st.tabs(["Upcoming Bookings", "Booking History"])
    
    # Display the upcoming bookings
    with tab1:
        st.subheader("Upcoming Bookings")
        if not upcoming_bookings:
            st.warning("No upcoming bookings.")
        else:
            upcoming_reservations_df = pd.DataFrame(upcoming_bookings)
            upcoming_reservations_df = upcoming_reservations_df.drop(columns=["email", "description"])
            upcoming_reservations_df.columns = ["Booking ID", "Date", "Start Time", "End Time", "Venue", "Booked by"]
            # Convert "Booking ID" column to float and format
            upcoming_reservations_df["Booking ID"] = upcoming_reservations_df["Booking ID"].astype(float).map("{:.0f}".format)
            upcoming_reservations_df["Date"] = pd.to_datetime(upcoming_reservations_df["Date"]).dt.strftime('%d/%m/%Y')
            upcoming_reservations_df["Start Time"] = pd.to_datetime(upcoming_reservations_df["Start Time"]).dt.strftime('%H:%M')
            upcoming_reservations_df["End Time"] = pd.to_datetime(upcoming_reservations_df["End Time"]).dt.strftime('%H:%M')
            st.table(upcoming_reservations_df.assign(hack='').set_index('hack'))
            #create_calendar_table(upcoming_reservations_df)

    # Display the past bookings
    with tab2:
        st.subheader("Booking History (Past Bookings)")
        if not past_bookings:
            st.warning("No past bookings.")
        else:
            past_reservations_df = pd.DataFrame(past_bookings)
            past_reservations_df = past_reservations_df.drop(columns=["email", "description"])
            past_reservations_df.columns = ["Booking ID", "Date", "Start Time", "End Time", "Venue", "Booked by"]
            st.table(past_reservations_df.assign(hack='').set_index('hack'))



def send_confirmation_email(user_email, booking_id, name, description, selected_room, start_time, end_time):
    try:
        # Your email credentials
        sender_email = st.secrets["sender"]["email"]
        sender_password = st.secrets["sender"]["password"]

        # Create the email content
        message = MIMEMultipart()
        message["From"] = 'HSE Booking System'
        message["To"] = user_email
        message["Subject"] = f"Booking Confirmation: (ID-{booking_id})"

        # Create the email content as an HTML table
        message_text = f"""
        <html>
        <body>
            <p>Hello {name}!</p>
            <p>We're thrilled to confirm your booking. Here are the details of your reservation:</p>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Booking ID:</strong></td>
                    <td>{booking_id}</td>
                </tr>
                <tr>
                    <td><strong>Meeting Title:</strong></td>
                    <td>{description}</td>
                </tr>
                <tr>
                    <td><strong>Location:</strong></td>
                    <td>{selected_room}</td>
                </tr>
                <tr>
                    <td><strong>Start Time:</strong></td>
                    <td>{start_time}</td>
                </tr>
                <tr>
                    <td><strong>End Time:</strong></td>
                    <td>{end_time}</td>
                </tr>
            </table>
            <p>Have a nice day!</p>
            <p>Best regards,<br>Your Meeting Room Booking Team</p>
        </body>
        </html>
        """

        # Include the HTML content in the email
        html_content = MIMEText(message_text, "html")
        message.attach(html_content)

        # Connect to the SMTP server
        server = smtplib.SMTP("smtp.gmail.com", port=587)
        server.starttls()

        # Login to the SMTP server using App Password
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, user_email, message.as_string())

        # Close the SMTP session
        server.quit()
        st.success("Email sent successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

st.set_page_config(
    page_title="Meeting Room Booking",
    page_icon=":calendar:",
    initial_sidebar_state="expanded",
    layout="wide",
)

width = streamlit_js_eval(js_expressions='screen.width', want_output = True, key = 'SCR')
if width > 800:
    # # Input password
    # password = st.text_input("Enter Password:", type="password")
    
    # # Check if the password is correct
    # if authenticate(password):
    #     st.empty()  # Clear the placeholder
    #     st.success("Logged in successfully!")
    st.title("Meeting Room & Desk Booking System 🖥️")
    
    date = current_time_ireland.date()
    time1=current_time_ireland.time()
    current_time1 = f"{time1.hour:02d}:{time1.minute:02d}"
    
    st.sidebar.button(f"Today's Date 🗓️ {date}")
    st.sidebar.button(f"Current Time ⏰ {current_time1}")
    
    # Sidebar menu
    menu_choice = st.sidebar.selectbox("Menu", ["Book a Room or Desk", "Cancel Booking", "View Bookings"])
   
    
    if menu_choice == "Book a Room or Desk":
        book_room()
    elif menu_choice == "Cancel Booking":
        cancel_room()
    elif menu_choice == "View Bookings":
        view_reservations()
else:
    st.title("Meeting Room & Desk Booking System 🖥️")

    date = current_time_ireland.date()
    time1=current_time_ireland.time()
    current_time1 = f"{time1.hour:02d}:{time1.minute:02d}"
    
    st.button(f"Today's Date 🗓️ {date}")
    st.button(f"Current Time ⏰ {current_time1}")
    
    # Not Sidebar menu
    menu_choice = st.selectbox("Menu", ["Book a Room or Desk", "Cancel Booking", "View Bookings"])
    
    if menu_choice == "Book a Room or Desk":
        book_room()
    elif menu_choice == "Cancel Booking":
        cancel_room()
    elif menu_choice == "View Bookings":
        view_reservations()
