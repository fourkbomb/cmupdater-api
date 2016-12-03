#
# Copyright (C) 2016 Simon Shields
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import print_function
import hashlib
import json
import os
import sys
if sys.version_info.major > 2:
    from http.server import HTTPServer, BaseHTTPRequestHandler
else:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    bytes = lambda a,b=None: str(a)



# load config
f = open('config.json')
j = json.load(f)
API_LEVEL = j['api']
HOST = j['host']
PORT = j['port']
f.close()

BASE_PATH = '.'

class UpdaterRequestHandler(BaseHTTPRequestHandler):
    def get_file_info(self, srv_path, channel):
        f = BASE_PATH + '/' + srv_path
        with open(f + '.md5sum', 'r') as fh:
            data = {
                'api_level': API_LEVEL,
                'changes': 'http://%s:%d/404'%(self.host, self.port),
                'channel': channel,
                'filename': srv_path.split('/')[-1],
                'incremental': '763a7b1c4b',
                'md5sum': fh.read().split()[0],
                'timestamp': int(os.path.getmtime(f)),
                'url': 'http://%s:%d/%s'%(self.host, self.port, srv_path),
            }
            return data

    def get_device_listing(self, device, channel):
        path = BASE_PATH + '/' + device
        if not os.path.exists(path):
            return {'id': None, 'result': [], 'error': 'No such device!'}

        results = []
        for f in os.listdir(path):
            if f[-4:] == '.zip' and os.path.exists(path + '/' + f + '.md5sum'):
                results.append(self.get_file_info(device + '/' + f, channel))
        return {'id': None,
                'result': results,
                'error': None}

    def do_GET(self):
        real_path = BASE_PATH + '/' + self.path
        if '..' in self.path or self.path.startswith('generic/') or self.path.startswith('api/') or \
                not os.path.exists(real_path):
            print("Serving file:", self.path)
            self.send_error(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            return

        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-octet-stream')
            self.send_header('Content-Length', os.path.getsize(real_path))
            self.end_headers()
            with open(real_path, 'rb') as f:
                for block in iter(lambda: f.read(65536), b''):
                    self.wfile.write(block)
        except Exception as e:
            print("Failed to transfer file %s, aborting."%self.path)
            print(e)
            return

    def do_POST(self):
        if self.path != '/api':
            self.send_error(404)
            self.end_headers()
            self.wfile.write('file not found')
            return
        if 'host' in self.headers:
            self.host = self.headers['host'].split(':')[0]
            self.port = self.headers['host'].split(':')[-1]
            if not self.port.isdigit():
                self.port = 80
            else:
                self.port = int(self.port)
        else:
            self.host = HOST
            self.port = PORT
        try:
            datalen = int(self.headers['content-length'])
            obj = json.loads(self.rfile.read(datalen).decode('utf-8'))
            method = obj['method']
            params = obj['params']
            if method == 'get_all_builds' or method == 'get_builds':
                device = params['device']
                res = bytes(json.dumps(self.get_device_listing(device, params['channels'][0])), 'utf-8')
                print("get_all_builds:", json.dumps(obj), "=>", res.decode('utf-8'))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
            else:
                self.send_error(404)
                self.end_headers()
                self.wfile.write('invalid method')
                return
        except Exception as e:
            print('Failed processing POST request', e)
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            res = bytes('internal server error', 'utf-8')
        self.end_headers()
        self.wfile.write(res)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        BASE_PATH = sys.argv[1]

    print('CMUpdater API ready to go (serving out of %s)!'%BASE_PATH)
    httpd = HTTPServer(('0.0.0.0', PORT), UpdaterRequestHandler)
    httpd.serve_forever()
