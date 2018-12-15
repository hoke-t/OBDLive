from channels.generic.websocket import WebsocketConsumer
import json
import mmap
from . import obdport

class DashboardConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()

    def receive(self, text_data=None):
        print(repr(text_data))
        text_data_json = json.loads(text_data)
        pids = text_data_json['pids']

        pid_data = dict()
        for pid in pids:
            pid_data[pid] = obdport.get_pid(pid)

        self.send(text_data=json.dumps({
            'data': pid_data,
            }))


class DTCConsumer(WebsocketConsumer):

    def connect(self):
                self.accept()

    def receive(self, text_data=None):
        if text_data == 'clear':
            obdport.get_pid('12') # Clears DTCs
        else:
            csv = obdport.get_pid('11') # DTC PID
            dtcs = [dtc for dtc in csv.split(',')][:-1]
            descs = []
            links = []

            with open('pid_data', 'rb', 0) as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                for dtc in dtcs:
                    idx = s.find(bytearray(dtc, 'utf-8')) + 6
                    if idx == -1:
                        descs.append('')
                    else:
                        descs.append(str(s[idx : s.find(b',', idx)], 'utf-8'))
                    links.append('obd-codes.com/' + dtc)

            self.send(text_data=json.dumps({
                'dtcs': dtcs,
                'descs': descs,
                'links': links,
                }))

