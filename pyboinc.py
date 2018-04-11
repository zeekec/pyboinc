import socket
import re
import xmltodict, json


class BoincException(Exception):
    pass


def convert_xml_to_dict(msg):
    return json.loads(json.dumps(xmltodict.parse(msg)))


def convert_dict_to_xml(msg):
    return xmltodict.unparse(msg, short_empty_elements=True, full_document=False).encode()


class BoincSocket:
    CMD_TERM = b'\x03'
    RE = re.compile(b'\s+/>')

    def __init__(self, host=None, port=31416, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def clean_message(self, msg):
        msg = self.RE.sub(b'/>', msg)
        return msg

    def send(self, msg):
        msg = self.clean_message(msg)
        msg += self.CMD_TERM
        self.sock.sendall(msg)

    def receive(self):
        chunks = []

        while True:
            chunk = self.sock.recv(8192)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            if chunk.find(self.CMD_TERM) != -1:
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
        d = {'boinc_gui_rpc_request': req}
        return convert_dict_to_xml(d)

    def wrap_command(self, cmd):
        d = {cmd: {}}
        return self.wrap_request(d)

    def command(self, cmd):
        msg = self.wrap_command(cmd)
        rep = self.call(msg)

        return convert_xml_to_dict(rep)


if __name__ == '__main__':
    with BoincSocket() as bc:
        print(
            convert_xml_to_dict(
                bc.call(b"<boinc_gui_rpc_request><exchange_versions  /></boinc_gui_rpc_request>").decode()
            )
        )
        print(
            convert_xml_to_dict(bc.call(b"<boinc_gui_rpc_request><get_host_info  /></boinc_gui_rpc_request>").decode())
        )
        print(convert_xml_to_dict(bc.call(b"<boinc_gui_rpc_request><auth1  /></boinc_gui_rpc_request>").decode()))
        print(
            convert_xml_to_dict(
                bc.call(b"<boinc_gui_rpc_request><aasdfafsdfasdfasdf /></boinc_gui_rpc_request>").decode()
            )
        )

    with BoincRpc() as br:
        print(br.command('exchange_versions'))
        print(br.command('auth1'))
        print(br.command('get_host_info'))
