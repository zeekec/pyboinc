import socket
import re


class BoincSocket:
    """demonstration class only
      - coded for clarity, not efficiency
    """

    def __init__(self, host=None, port=31416, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

        self.re = re.compile(b'\s+/>')

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg):
        msg = self.re.sub(b'/>', msg)
        msg += b'\x03'
        self.sock.sendall(msg)

    def receive(self):
        chunks = []

        while True:
            chunk = self.sock.recv(8192)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            if chunk.find(b'\x03') != -1:
                break

        return b''.join(chunks)[0:-1]

    def call(self, msg):
        self.send(msg)
        return self.receive()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()


class BoincRpc(BoincSocket):
    def __init__(self, host=None, port=31416, timeout=None):
        BoincSocket.__init__(self, host, port, timeout)

    def wrap_request(self, req):
        return b"<boinc_gui_rpc_request><exchange_versions  />%s</boinc_gui_rpc_request>" % req

    def wrap_command(self, cmd):
        return self.wrap_request(b'<'+cmd+b'/>')

    def command(self, cmd):
        msg=self.wrap_command(cmd)
        return self.call(msg)

if __name__ == '__main__':
    with BoincSocket() as bc:
        print(
            bc.call(b"<boinc_gui_rpc_request><exchange_versions  /><get_host_info  /></boinc_gui_rpc_request>")
            .decode())
        print(bc.call(b"<boinc_gui_rpc_request><get_host_info  /></boinc_gui_rpc_request>").decode())
        print(bc.call(b"<boinc_gui_rpc_request><auth1  /></boinc_gui_rpc_request>").decode())
        print(bc.call(b"<boinc_gui_rpc_request><aasdfafsdfasdfasdf /></boinc_gui_rpc_request>").decode())

    with BoincRpc() as br:
        print(br.command(b'exchange_versions').decode())
