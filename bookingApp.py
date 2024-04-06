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
