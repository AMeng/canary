#!/usr/bin/env python3

from getpass import getuser
from time import time
import argparse
import json
import os
import socket
import subprocess
import sys


HELP = {
    "BATCH": "Execute a series of commands from a JSON file.",
    "BATCH_PATH": "Path to a JSON file with one or more commands to execute.",
    "PROCESS": "Run an executable and immediately terminate it.",
    "PROCESS_PATH": "Full path to the executable.",
    "PROCESS_ARGS": "Optional arguments to pass to the executable.",
    "FILE": "Perform actions on a file.",
    "FILE_ACTION": "Action to take on the file.",
    "FILE_PATH": "Path to the file.",
    "NETWORK": "Connect to an endpoint and send a request.",
    "NETWORK_HOST": "Hostname of the request recipient.",
    "NETWORK_PORT": "Port of the request recipient.",
    "NETWORK_PROTOCOL": "Protocol used to send the request.",
    "NETWORK_DATA": "Data to send to the recipient.",
}


def handle_process(path, args):
    command = [path] + (args or [])
    start_time = int(time())
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        return {"status": "failure", "reason": f"executable not found at {path}"}
    except PermissionError:
        return {"status": "failure", "reason": f"Permission denied trying to execute {path}"}
    process.terminate()
    process.wait()
    return {
        "status": "success",
        "timestamp": start_time,
        "username": getuser(),
        "process_name": path,
        "process_command": " ".join(command),
        "process_id": process.pid,
    }


def handle_file(action, path):
    start_time = int(time())
    if action == "create":
        try:
            with open(path, "w"):
                pass
        except PermissionError:
            return {"status": "failure", "reason": f"Permission denied creating file at {path}"}
    elif action == "modify":
        try:
            with open(path, "a"):
                os.utime(path, None)
        except FileNotFoundError:
            return {"status": "failure", "reason": f"file not found at {path}"}
        except PermissionError:
            return {"status": "failure", "reason": f"Permission denied modifying file at {path}"}
    elif action == "delete":
        try:
            os.remove(path)
        except FileNotFoundError:
            return {"status": "failure", "reason": f"file not found at {path}"}
        except PermissionError:
            return {"status": "failure", "reason": f"Permission denied deleting file at {path}"}
    return {
        "status": "success",
        "timestamp": start_time,
        "username": getuser(),
        "process_name": sys.argv[0],
        "process_command": " ".join(sys.argv),
        "process_id": os.getpid(),
        "path": path,
        "activity": action,
    }


def handle_network(host, port, protocol="tcp", data=None):
    socket_protocol = socket.SOCK_STREAM
    if protocol == "udp":
        socket_protocol = socket.SOCK_DGRAM
    with socket.socket(socket.AF_INET, socket_protocol) as s:
        data = (data or "").encode()
        s.bind(("", 0))
        source_host = socket.gethostbyname("localhost")
        source_port = s.getsockname()[1]
        start_time = int(time())
        try:
            s.connect((host, port))
            s.send(data)
        except ConnectionRefusedError:
            return {"status": "failure", "reason": f"Connection refused at {host}:{port}"}
        return {
            "status": "success",
            "timestamp": start_time,
            "username": getuser(),
            "process_name": sys.argv[0],
            "process_command": " ".join(sys.argv),
            "process_id": os.getpid(),
            "destination": f"{host}:{port}",
            "source": f"{source_host}:{source_port}",
            "size": len(data),
            "protocol": protocol,
        }


def handle_batch(path):
    with open(path, "r") as batch_file:
        batch = json.load(batch_file)
    for call in batch:
        command = call["command"]
        args = [command]
        if command == "file":
            args.append(call["action"])
            args.append(call["path"])
        elif command == "process":
            args.append(call["path"])
            if call.get("args"):
                args.append("-a")
                args.append(call["args"])
        elif command == "network":
            args.append(call["host"])
            args.append(call["port"])
            if call.get("protocol"):
                args.append("-p")
                args.append(call["protocol"])
            if call.get("data"):
                args.append("-d")
                args.append(call["data"])
        execute(args)


def execute(args):
    parser = argparse.ArgumentParser("canary.py", description="OS Event Emitter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_batch = subparsers.add_parser("batch", description=HELP["BATCH"])
    parser_batch.add_argument("path", help=HELP["BATCH_PATH"])

    parser_process = subparsers.add_parser("process", description=HELP["PROCESS"])
    parser_process.add_argument("path", help=HELP["PROCESS_PATH"])
    parser_process.add_argument("-a", "--args", nargs=argparse.REMAINDER, help=HELP["PROCESS_ARGS"])

    parser_file = subparsers.add_parser("file", description=HELP["FILE"])
    parser_file_actions = ["create", "delete", "modify"]
    parser_file.add_argument("action", choices=parser_file_actions, help=HELP["FILE_ACTION"])
    parser_file.add_argument("path", help=HELP["FILE_PATH"])

    parser_network = subparsers.add_parser("network", description=HELP["NETWORK"])
    parser_network.add_argument("host", help=HELP["NETWORK_HOST"])
    parser_network.add_argument("port", type=int, help=HELP["NETWORK_PORT"])
    parser_network.add_argument("-d", "--data", help=HELP["NETWORK_DATA"])
    parser_network.add_argument(
        "-p", "--protocol", default="tcp", choices=["tcp", "udp"], help=HELP["NETWORK_PROTOCOL"]
    )

    p = parser.parse_args(args)
    if p.command == "batch":
        handle_batch(p.path)
    else:
        if p.command == "process":
            log = handle_process(p.path, p.args)
        elif p.command == "file":
            log = handle_file(p.action, p.path)
        elif p.command == "network":
            log = handle_network(p.host, p.port, p.protocol, p.data)
        print(json.dumps(log))


if __name__ == "__main__":
    execute(sys.argv[1:])
