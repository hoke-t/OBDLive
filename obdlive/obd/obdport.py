import socket
import sys


pid_map = {
    '1':  b'02010c0000000000', # Engine RPM
    '2':  b'02010d0000000000', # Vehicle speed
    '3':  b'0201450000000000', # Throttle Position
    '4':  b'02015c0000000000', # Engine oil temperature
    '5':  b'0201520000000000', # Ethanol fuel percent
    '6':  b'0201100000000000', # MAF air flow rate
    '7':  b'02011f0000000000', # Run time since engine start
    '8':  b'02015e0000000000', # Engine fuel rate
    '9':  b'0201460000000000', # Ambient air temperature
    '10': b'0201040000000000', # Calculated engine load
    '11': b'0103000000000000', # Request trouble codes
    '12': b'0104000000000000', # Clear trouble codes
}

__sock = None

# Returns vehicle speed in mph
def __vehicle_speed(data):
    return str(int(data[6:8], 16) * 0.62137119224)

# Returns engine RPM in revolutions per minute
def __engine_rpm(data):
    return str((int(data[6:8], 16) * 256 + int(data[8:10], 16)) / 4.0)

# Returns engine oil temperature in deg C
def __engine_oil_temperature(data):
    return str(int(data[6:8], 16) - 40)

# Returns throttle position as a percentage
def __throttle_position(data):
    return str(int(100 * int(data[6:8], 16) / 255.0))

# Returns ethanol fuel %
def __ethanol_fuel_percent(data):
    return str(100 * int(data[6:8], 16) / 255.0)

# Returns MAF air flow rate in grams/sec
def __maf_air_flow_rate(data):
    return str((int(data[6:8],16) * 256 + int(data[8:10], 16)) / 100.0)

# Returns run time since engine start in sec
def __run_time_since_engine_start(data):
    return str(int(data[6:8], 16) * 256 + int(data[8:10], 16))

# Returns engine fuel rate in L/h
def __engine_fuel_rate(data):
    return str((int(data[6:8],16) * 256 + int(data[8:10], 16)) / 20.0)

# Returns ambient air temperature in deg C
def __ambient_air_temperature(data):
    return str(int(data[6:8], 16) - 40)

# Returns calculated engine load as a percentage
def __engine_load(data):
    return str(int(100 * int(data[6:8], 16) / 255.0))

# Returns the DTC in human-readable format
def __diagnostic_trouble_code(data):
    dtc = ''
    dtc_map = {
            0: 'P',
            1: 'C',
            2: 'B',
            3: 'U',
    }

    print('Converting data: ' + str(data[0:4]))

    dtc += dtc_map[int(str(data[0]), 16) >> 4]
    dtc += str(int(str(data[0]), 16) & 0xF)
    dtc += str(int(str(data[1]), 16))
    dtc += str(int(str(data[2]), 16))
    dtc += str(int(str(data[3]), 16))

    return dtc


def get_pid(pid):
    global __sock
    if __sock == None:
        # Create a TCP/IP __socket
        __sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('192.168.4.1', 31415)
        __sock.connect(server_address)

    response = '...'

    if pid in pid_map.keys():
        # Send PID
        __sock.sendall(pid_map[pid])

        # Handle ISO-TP responses for diagnostics
        if pid == '11':
            first_frame = __sock.recv(16).decode('utf-8')
            print(first_frame)

            isotp_size = -1
            codes_expected = 0

            # Check if this is a first frame.
            # If so, we need to store the expected size.
            if int(first_frame[0], 16) == 1:
                #isotp_size = (int(first_frame[0], 16) & 0xF) << 8 | int(first_frame[1], 16) 
                codes_expected = int(first_frame[6:8], 16)
            else: # This means it's a single frame, so there are less than 3 codes (potentially 0)
                codes_expected = int(first_frame[4:6], 16)

            print(codes_expected)

            response = ''
            codes_received = 0

            # Single frame: data starts at byte 1
            if first_frame[0] == '0':
                for i in range(6, 16, 4):
                    if codes_received < codes_expected:
                        dtc = first_frame[i:i+4]
                        response += __diagnostic_trouble_code(dtc) + ','
                        codes_received += 1
            elif (first_frame[0] == '1'):
                for i in range(8, 16, 4):
                    dtc = first_frame[i:i+4]
                    response += __diagnostic_trouble_code(dtc) + ','
                    codes_received += 1

            awaiting_data = codes_expected >= 3;
            # Wait for all of the packets...
            # TODO: This loop breaks if for whatever reason the last packet gets lost in transit.. Need some kind of timeout here.
            while (awaiting_data):
                frame = __sock.recv(16)
                #awaiting_data = not (int(frame[1], 16) == isotp_size-1);    # We need more data unless the packet's index is isotp_size - 1,
                                                                            # since this would be the last packet. 
                for i in range(2, 16, 4):
                    codes_received += 1
                    response += __diagnostic_trouble_code((frame[i:i+4]).decode('utf-8')) + ','
                    if (codes_received == codes_expected):
                        awaiting_data = False
                        break

        else:
            # Handle data
            data = __sock.recv(16).decode('utf-8')
            print(data)
            # Delegate to pid handler
            if pid == '1':
                response = __engine_rpm(data)
            elif pid == '2':
                response = __vehicle_speed(data)
            elif pid == '3':
                response = __throttle_position(data)
            elif pid == '4':
                response = __engine_oil_temperature(data)
            elif pid == '5':
                response = __ethanol_fuel_percent(data)
            elif pid == '6':
                response = __maf_air_flow_rate(data)
            elif pid == '7':
                response = __run_time_since_engine_start(data)
            elif pid == '8':
                response = __engine_fuel_rate(data)
            elif pid == '9':
                response = __ambient_air_temperature(data)
            elif pid == '10':
                response = __engine_load(data)

    return response
