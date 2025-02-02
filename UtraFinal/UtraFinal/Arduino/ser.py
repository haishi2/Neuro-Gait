import serial
import time
import csv
from datetime import datetime


def recordData(bluetooth_port, length, waittime, char): 
    baud_rate = 9600  
    arr = []
    try:
        ser = serial.Serial(bluetooth_port, baud_rate, timeout=1)
        print(char + f" Connected to {bluetooth_port} at {baud_rate} baud.")

        print(char + " Loading")
        time.sleep(waittime)
        print(char + " Starting recording")
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if ser.in_waiting > 0: 
                
                data = ser.readline().decode('utf-8').strip()
                arr.append(data + "," + str(elapsed))
                
            if (elapsed) >= length:
                print(f"Recording stopped after {length} seconds.")
                print("\nDisconnected. " + char)
                break
    
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        
    except KeyboardInterrupt:

        print("\nDisconnected. " + char)
        
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
    
    time_string = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d-%H-%M-%S")
    with open(char + time_string+".csv", "w") as file:
        for row in arr:
            file.write(row + "\n")
    print(char + time_string+".csv", "Recorded")