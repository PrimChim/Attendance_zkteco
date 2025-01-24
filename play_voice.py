from zk import ZK, const

# Device configuration
DEVICE_IP = input("Enter the device IP address(default 192.168.1.201): ") or '192.168.1.201'
DEVICE_PORT = int(input("Enter the device port (default 4370): ") or 4370)

conn = None

# Create ZK instance
zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5, password=0, force_udp=False, ommit_ping=False)


try:
    # connect to device
    conn = zk.connect()

    
    for i in range(0, 54):
        conn.test_voice(index=i)
        
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
