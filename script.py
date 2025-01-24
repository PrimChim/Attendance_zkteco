from zk import ZK
import csv
from datetime import datetime

# Device configuration
DEVICE_IP = input("Enter the device IP address(default 192.168.1.201): ") or '192.168.1.201'
DEVICE_PORT = int(input("Enter the device port (default 4370): ") or 4370)
CSV_FILE = input("Enter the name for the CSV file (default attendance_data.csv): ") or "attendance_data_this_month.csv"

conn = None

# Create ZK instance
zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5, password=0, force_udp=False, ommit_ping=False)

try:
    # Connect to the device
    conn = zk.connect()
    
    # Disable the device to ensure no activity during the process
    conn.disable_device()
    
    # Fetch all users
    users = conn.get_users()
    user_dict = {user.user_id: user.name for user in users}  # Create a mapping of user_id to username
    
    # Fetch attendance logs
    attendance = conn.get_attendance()
    
    # Filter logs for the current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    filtered_attendance = [
        record for record in attendance 
        if record.timestamp.month == current_month and record.timestamp.year == current_year
    ]
    
    if filtered_attendance:
        # Write filtered attendance logs to a CSV file
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header row
            writer.writerow(['Username', 'Timestamp', 'Punch Type', 'Status'])
            
            # Write attendance records with usernames
            for record in filtered_attendance:
                username = user_dict.get(record.user_id, 'Unknown')  # Get username or fallback to 'Unknown'
                writer.writerow([
                    username,
                    record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Format timestamp
                    record.punch,
                    record.status
                ])
        
        print(f"Attendance data for this month has been written to {CSV_FILE}")
    else:
        print("No attendance data found for the current month.")
    
    # Re-enable the device after commands are executed
    conn.enable_device()

except Exception as e:
    print(f"Process terminated: {e}")

finally:
    if conn:
        conn.disconnect()
