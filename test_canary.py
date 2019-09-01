#!/usr/bin/env python3

from unittest.mock import call, patch, Mock
import canary
import os
import socket
import subprocess
import tempfile
import time
import unittest


class TestCanary(unittest.TestCase):
    def _run(self, command):
        canary.execute(command.split())

    def assertNetworkCall(self, socket_mock, host, port, protocol, data):
        socket_protocol = socket.SOCK_STREAM
        if protocol == "udp":
            socket_protocol = socket.SOCK_DGRAM
        calls = [
            call(socket.AF_INET, socket_protocol),
            call().__enter__().bind(("", 0)),
            call().__enter__().connect((host, port)),
            call().__enter__().send(data.encode()),
        ]
        socket_mock.assert_has_calls(calls, any_order=True)

    def test_file_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = os.path.join(tmp, "test_canary_create.txt")
            self.assertFalse(os.path.isfile(file_path))
            self._run(f"file create {file_path}")
            self.assertTrue(os.path.isfile(file_path))

    def test_file_modify(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        old_timestamp = os.path.getmtime(f.name)
        time.sleep(0.1)
        self._run(f"file modify {f.name}")
        new_timestamp = os.path.getmtime(f.name)
        self.assertTrue(new_timestamp > old_timestamp)

    def test_file_delete(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        self.assertTrue(os.path.isfile(f.name))
        self._run(f"file delete {f.name}")
        self.assertFalse(os.path.isfile(f.name))

    @patch.object(socket, "socket")
    def test_network_default(self, socket_mock):
        self._run("network google.com 80")
        self.assertNetworkCall(socket_mock, "google.com", 80, "tcp", "")

    @patch.object(socket, "socket")
    def test_network_tcp(self, socket_mock):
        self._run("network google.com 80 --protocol tcp")
        self.assertNetworkCall(socket_mock, "google.com", 80, "tcp", "")

    @patch.object(socket, "socket")
    def test_network_tcp_with_data(self, socket_mock):
        self._run("network google.com 80 --protocol tcp --data hello")
        self.assertNetworkCall(socket_mock, "google.com", 80, "tcp", "hello")

    @patch.object(socket, "socket")
    def test_network_udp(self, socket_mock):
        self._run("network google.com 80 --protocol udp")
        self.assertNetworkCall(socket_mock, "google.com", 80, "udp", "")

    @patch.object(socket, "socket")
    def test_network_udp_with_data(self, socket_mock):
        self._run("network google.com 80 --protocol udp --data hello")
        self.assertNetworkCall(socket_mock, "google.com", 80, "udp", "hello")

    @patch.object(subprocess, "Popen")
    def test_process(self, popen_mock):
        popen_mock.return_value = Mock(pid=100)
        self._run("process p")
        popen_mock.assert_called_with(["p"], stdout=subprocess.DEVNULL)

    @patch.object(subprocess, "Popen")
    def test_process_with_one_arg(self, popen_mock):
        popen_mock.return_value = Mock(pid=100)
        self._run("process p --args a")
        popen_mock.assert_called_with(["p", "a"], stdout=subprocess.DEVNULL)

    @patch.object(subprocess, "Popen")
    def test_process_with_multiple_args(self, popen_mock):
        popen_mock.return_value = Mock(pid=100)
        self._run("process p --args a b c")
        popen_mock.assert_called_with(["p", "a", "b", "c"], stdout=subprocess.DEVNULL)

    @patch.object(canary, "handle_process")
    @patch.object(canary, "handle_file")
    @patch.object(canary, "handle_network")
    def test_batch(self, network_mock, file_mock, process_mock):
        process_mock.return_value = {}
        file_mock.return_value = {}
        network_mock.return_value = {}
        self._run("batch test/test_batch.json")
        process_calls = [call("ls", None), call("ls", ["-l"])]
        file_calls = [
            call("create", "/tmp/test.txt"),
            call("delete", "/tmp/test.txt"),
            call("modify", "/tmp/test.txt"),
        ]
        network_calls = [
            call("google.com", 80, "tcp", None),
            call("google.com", 80, "tcp", None),
            call("google.com", 80, "udp", None),
            call("google.com", 80, "tcp", "test"),
            call("google.com", 80, "udp", "test"),
        ]
        process_mock.assert_has_calls(process_calls)
        file_mock.assert_has_calls(file_calls)
        network_mock.assert_has_calls(network_calls)


if __name__ == "__main__":
    unittest.main()
