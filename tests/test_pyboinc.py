import pyboinc

import socket
import pytest
from mock import ANY
from mock import patch


class TestConvert:
    def test_convert_xml_to_dict(self):
        assert {'a': {'b': None}} == pyboinc.convert_xml_to_dict(b'<a><b/></a>')
        assert {'a': 'b'} == pyboinc.convert_xml_to_dict(b'<a>b</a>')

    def test_convert_dict_to_xml(self):
        assert b'<a><b/></a>' == pyboinc.convert_dict_to_xml({'a': [{'b': {}}]})
        assert b'<a>b</a>' == pyboinc.convert_dict_to_xml({'a': 'b'})
        assert b'<a><b/></a>' == pyboinc.convert_dict_to_xml({'a': {'b': {}}})
        assert b'<a><b/></a>' == pyboinc.convert_dict_to_xml({'a': {'b': None}})


@patch('socket.create_connection')
class TestBoincSocket:
    def test_receive(self, mock_socket):
        mock_socket.return_value.recv.return_value = b'some_data\x03'
        with pyboinc.BoincSocket() as bc:
            expected = b'some_data'
            result = bc.receive()
            assert expected == result

    def test_receive_multipart(self, mock_socket):
        mock_socket.return_value.recv.side_effect = [b'some_', b'data\x03']
        with pyboinc.BoincSocket() as bc:
            expected = b'some_data'
            result = bc.receive()
            assert expected == result

    def test_receive_error(self, mock_socket):
        mock_socket.return_value.recv.return_value = b''
        with pyboinc.BoincSocket() as bc:
            with pytest.raises(RuntimeError):
                bc.receive()

    def test_send(self, mock_socket):
        with pyboinc.BoincSocket('3323', 1234, 3) as bc:
            bc.send(b'asdfasdf')

        mock_socket.assert_called_with(('3323', 1234), timeout=3)
        mock_socket.return_value.sendall.assert_called_with(b'asdfasdf\x03')
        mock_socket.return_value.close.assert_called_with()

    def test_clean_message(self, mock_socket):
        bs = pyboinc.BoincSocket()
        assert b'<a><b/></a>' == bs.clean_message(b'<a><b/></a>')
        assert b'<a><b/></a>' == bs.clean_message(b'<a><b /></a>')
        assert b'<a><b/></a>' == bs.clean_message(b'<a><b \t/></a>')
        assert b'<a><b/></a>' == bs.clean_message(b'<a><b \n\t/></a>')

    def test_call_multipart(self, mock_socket):
        mock_socket.return_value.recv.side_effect = [b'some_', b'data\x03']
        with pyboinc.BoincSocket() as bc:
            expected = b'some_data'
            result = bc.call(b'<ssddff   />')
            assert expected == result

        mock_socket.assert_called_with((None, 31416), timeout=None)
        mock_socket.return_value.sendall.assert_called_with(b'<ssddff/>\x03')
        mock_socket.return_value.close.assert_called_with()


@patch('socket.create_connection')
class TestBoincRpc:
    def test_wrap_request(self, mock_socket):
        bc = pyboinc.BoincRpc()

        assert {'boinc_gui_rpc_request': 'bob'} == bc.wrap_request('bob')
        assert {'boinc_gui_rpc_request': {'bob': {}}} == bc.wrap_request({'bob': {}})

    def test_call(self, mock_socket):
        mock_socket.return_value.recv.side_effect = [
            b'<boinc_gui_rpc_reply>\n<server_version>\n   <major>7</major>\n   <minor>8</minor>\n   <release>4</release>\n</server_version>\n</boinc_gui_rpc_reply>\n\x03'
        ]
        with pyboinc.BoincRpc() as bc:
            expected = {'server_version': {'major': '7', 'release': '4', 'minor': '8'}}
            assert expected == bc.call({'exchange_versions': {}})

    def test_call_error_fake(self, mock_socket):
        with patch('socket.create_connection') as mock_socket2:
            mock_socket2.return_value.recv.side_effect = [
                b'<aboinc_gui_rpc_reply>\n<error>unrecognized op: aasdfafsdfasdfasdf/</error>\n</aboinc_gui_rpc_reply>\n\x03'
            ]
            with pyboinc.BoincRpc() as bc:
                with pytest.raises(pyboinc.BoincBadReply,match="Did not get a 'boinc_gui_rpc_reply': {'aboinc_gui_rpc_reply': {'error': 'unrecognized op: aasdfafsdfasdfasdf/'}}"):
                    bc.call({'aasdfafsdfasdfasdf': {}})

    def test_call_error(self, mock_socket):
        mock_socket.return_value.recv.side_effect = [
            b'<boinc_gui_rpc_reply>\n<error>unrecognized op: aasdfafsdfasdfasdf/</error>\n</boinc_gui_rpc_reply>\n\x03'
        ]
        with pyboinc.BoincRpc() as bc:
            with pytest.raises(pyboinc.BoincBadRequest,match=''):
                bc.call({'aasdfafsdfasdfasdf': {}})
