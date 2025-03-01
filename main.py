import csv
import calendar
from io import StringIO
from zk import ZK, const
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, render_template, Response

# Device configuration
DEVICE_IP = '192.168.1.201'
DEVICE_PORT = 4370

app = Flask(__name__)

attendance_logs = []

@app.route("/")
def home():
    return "Welcome to the ZKTeco Management App!"

@app.route("/users", methods=["POST"])
def add_user():
    data = request.form
    user_id = data.get("user_id")
    name = data.get("name")
    password = data.get("password")
    privilege = data.get("privilege", "User")  # Default to "User" privilege

    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5)

    try:
        # Connect to the device
        conn = zk.connect()
        conn.disable_device()

        # Fetch existing users
        users = conn.get_users()
        user_ids = [user.user_id for user in users]

        # Check if the user ID already exists
        if user_id in user_ids:
            return jsonify({"error": "User ID already exists"}), 400

        # Set privilege
        privilege_code = const.USER_ADMIN if privilege.lower() == "admin" else const.USER_DEFAULT

        # Add the user
        conn.set_user(
            uid=int(user_id),
            name=name,
            privilege=privilege_code,
            password=password,
            group_id="",
            user_id=user_id
        )

        conn.enable_device()

        # Fetch updated user list
        updated_users = conn.get_users()
        users_data = [{"user_id": user.user_id, "name": user.name.strip(), "previlage": user.previlage} for user in updated_users]

        return render_template('users.html', users=users_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.disconnect()

@app.route("/users", methods=["GET"])
def get_users():

    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5, password=0, force_udp=False, ommit_ping=False)

    try:
        # Connect to the device
        conn = zk.connect()
        conn.disable_device()  # Temporarily disable the device to prevent other operations
        
        # Fetch users from the device
        users = conn.get_users()
        user_list = []
        for user in users:
            privilege = "User"
            if user.privilege == const.USER_ADMIN:
                privilege = "Admin"
            user_data = {
                "uid": user.uid,
                "name": user.name.strip() or "Unknown",
                "privilege": privilege,
                "password": user.password,
                "group_id": user.group_id,
                "user_id": user.user_id
            }
            user_list.append(user_data)

        conn.enable_device()  # Re-enable the device after fetching data
        return render_template('users.html', users=user_list)

    except Exception as e:
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500

    finally:
        if conn:
            conn.disconnect()

@app.route("/users/<user_id>", methods=["PUT"])
def edit_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    name = data.get("name")
    privilege = data.get("privilege")

    if name:
        users[user_id]["name"] = name
    if privilege:
        users[user_id]["privilege"] = privilege

    return jsonify({"message": "User updated successfully!", "user": users[user_id]})

@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    del users[user_id]
    return jsonify({"message": "User deleted successfully!"})

@app.route("/attendance", methods=["POST"])
def fetch_attendance():
    # Simulated log from ZKTeco (use zk library for real data)
    logs = [
        {"user_id": "1", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"user_id": "2", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]
    for log in logs:
        attendance_logs.append(log)
    return jsonify({"message": "Attendance fetched successfully!", "logs": logs})

@app.route("/attendance", methods=["GET"])
def view_attendance():
    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT)
    try:
        conn = zk.connect()
        conn.disable_device()

        # Fetch attendance logs and users
        attendance = conn.get_attendance()
        users = conn.get_users()
        conn.enable_device()

        # Create a mapping of user_id to username
        user_map = {user.user_id: user.name.strip() or "Unknown" for user in users}

        # Determine current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get the number of days in the month
        _, num_days = calendar.monthrange(current_year, current_month)

        # Initialize attendance data for the month
        monthly_attendance = defaultdict(lambda: ["A"] * num_days)  # Default to "Absent" for all days

        # Process attendance logs
        for att in attendance:
            if att.timestamp.year == current_year and att.timestamp.month == current_month:
                day = att.timestamp.day  # Get the day of the month (1-31)
                user_id = att.user_id
                monthly_attendance[user_id][day - 1] = "P"

        # Prepare data for rendering
        attendance_data = []
        for user_id, days in monthly_attendance.items():
            attendance_data.append({
                'user_id': user_id,
                'username': user_map.get(user_id, "Unknown"),
                'days': days
            })

        # Render the template
        return render_template('attendance.html', attendance=attendance_data, num_days=num_days)

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if conn:
            conn.disconnect()

@app.route("/attendance/export", methods=["GET"])
def export_attendance():
    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT)
    try:
        conn = zk.connect()
        conn.disable_device()

        # Fetch attendance logs and users
        attendance = conn.get_attendance()
        users = conn.get_users()
        conn.enable_device()

        # Create a mapping of user_id to username
        user_map = {user.user_id: user.name.strip() or "Unknown" for user in users}

        # Get current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get the number of days in the current month
        _, num_days = calendar.monthrange(current_year, current_month)

        # Initialize attendance data for all users
        monthly_attendance = defaultdict(lambda: ["A"] * num_days)  # Default all days to "Absent"

        # Process attendance logs
        for att in attendance:
            if att.timestamp.year == current_year and att.timestamp.month == current_month:
                day = att.timestamp.day  # Get the day of the month (1-31)
                user_id = att.user_id
                monthly_attendance[user_id][day - 1] = "P"

        # Prepare CSV content
        output = StringIO()
        writer = csv.writer(output)

        # Write header row with days of the month
        header = ["User ID", "Username"] + [f"{i}" for i in range(1, num_days + 1)]
        writer.writerow(header)

        # Write attendance data for each user
        for user_id, days in monthly_attendance.items():
            writer.writerow([user_id, user_map.get(user_id, "Unknown")] + days)

        # Send the CSV as a downloadable response
        output.seek(0)
        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=attendance_{current_year}_{current_month}.csv"
        return response

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if conn:
            conn.disconnect()

#adding fingerprint of particular user
@app.route("/users/<user_id>/add_fingerprint", methods=["POST"])
def add_fingerprint(user_id):
    conn = None
    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=10)

    try:
        # Connect to the device
        conn = zk.connect()
        conn.disable_device()

        # Start fingerprint enrollment
        conn.enroll_user(uid=int(user_id), temp_id=2)
        conn.test_voice()
        conn.enable_device()

        return jsonify({"message": f"Fingerprint enrollment initiated for User ID {user_id}. Please complete the process on the device."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.disconnect()

if __name__ == "__main__":
    app.run()