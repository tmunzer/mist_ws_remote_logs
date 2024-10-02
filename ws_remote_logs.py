import os
import logging
import re
from datetime import datetime
from contextlib import closing
from dotenv import load_dotenv
import websocket
import requests


ENV_FILE = ".env"
MIST_HOST = ""
MIST_APITOKEN = ""
MIST_ORG_ID = ""
MIST_SITE_ID = ""
MIST_DEVICE_ID = ""
LOG_MATCH = ""
LOG_FILE = "./ws_remote_logs.log"
OUT_FILE = "./ws_remote_logs.txt"

WS_TIMEOUT = 30

class MistSocket:

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.ws = None
        self.timeout = 30
        self.re_start = r"^mist@\S+> "
        self.re_end = r"mist@\S+> $"
        self.log_files = []
        self.log_lines = []

    def start(self):
        with closing(websocket.create_connection(self.uri, timeout=self.timeout)) as ws:
            self.ws = ws
            self._wait_shell()
            self._get_log_files()
            self._count_in_log_files()
            self._find_in_log_files()
            self._exit_shell()
            print("result ".ljust(80, "."))
            for tmp in self.log_lines:
                print(tmp)
            print(len(self.log_lines))
            print(self.log_files)

    def _get_ts(self):
        return round(datetime.timestamp(datetime.now()))


    def _wait_shell(self):
        print("waiting for remote shell ".ljust(80, "."))
        result = ""
        # receive data
        while not  re.findall(self.re_end, result):
            result_bytes = self.ws.recv()
            if result_bytes:
                result = result_bytes.decode("utf-8")

    def _exit_shell(self):
        print("cleaning for remote shell session ".ljust(80, "."))
        # send data
        data = f"\00exit\n"
        logging.debug(f"sending: {data.replace("\x00", "")}")
        data_byte = bytearray()
        data_byte.extend(map(ord, data))
        self.ws.send_binary(data_byte)
        self.ws.close(websocket.STATUS_NORMAL)

    def _get_log_files(self):
        print("listing files ".ljust(80, "."))
        files = []
        # send data
        data = f"\00file list /var/log/messages*\n"
        logging.debug(f"sending:\n{data.replace("\x00", "")}")
        data_byte = bytearray()
        data_byte.extend(map(ord, data))
        self.ws.send_binary(data_byte)
        result = ""
        # receive data
        while not  re.findall(self.re_end, result):
            result_bytes = self.ws.recv()
            if result_bytes:
                tmp = result_bytes.decode("utf-8")
                result += tmp
        logging.debug(f"received:\n{result.replace("\x00", "")}")
        # process response
        for tmp in result.replace("\x00", "").split("\r\n"):
            if tmp.startswith("/var/log/"):
                self.log_files.append({"file": tmp, "junos_count": 0, "script_count": 0, "done": False})
                files.append(tmp)
        logging.info(f"log files: {', '.join(files)}")

    def _count_in_log_files(self):
        count_re = r'Count: (?P<count>\d*) lines'
        for log_file in self.log_files:
            print(f"get count for file \"{log_file['file']}\" ".ljust(80, "."))
            # send data
            data = f"\00file show {log_file['file']} | match {LOG_MATCH} | count\n"
            logging.debug(f"file {log_file['file']} - sending:\n{data.replace("\x00", "")}")
            data_byte = bytearray()
            data_byte.extend(map(ord, data))
            self.ws.send_binary(data_byte)
            result = ""
            # receive data
            while not re.findall(self.re_end, result):
                result_bytes = self.ws.recv()
                if result_bytes:
                    tmp = result_bytes.decode("utf-8")
                    result += tmp
            # process response
            logging.debug(f"file {log_file['file']} - received:\n{result.replace("\x00", "")}")
            count = re.findall(count_re, result)
            if count:
                try:
                    c = int(count[0])
                    log_file["junos_count"] = c
                    logging.debug(f"file {log_file['file']}: {c} entries")
                except:
                    logging.error(f"file {log_file['file']}: unable to convert count entry to int")
            else:
                logging.warning(f"file {log_file['file']}: unable to extract count number")

    def _find_in_log_files(self):
        for log_file in self.log_files:
            if log_file["done"]:
                logging.debug(f"file {log_file['file']}: file already done... skipping it")
            else:
                logging.debug(f"file {log_file['file']}: file not done yet... starting the process")
                count = 0
                print(f"get entries file \"{log_file['file']}\" ".ljust(80, "."))
                # send data
                req = f"file show {log_file['file']} | match {LOG_MATCH} | no-more"
                data = f"\00{req}\n"
                logging.debug(f"file {log_file['file']} - sending:\n{data.replace("\x00", "")}")
                data_byte = bytearray()
                data_byte.extend(map(ord, data))
                self.ws.send_binary(data_byte)
                result = ""
                # receive data
                while not re.findall(self.re_end, result):
                    result_bytes = self.ws.recv()
                    if result_bytes:
                        tmp = result_bytes.decode("utf-8")
                        result += tmp
                log_file["done"] = True
                # process response
                logging.debug(f"file {log_file['file']} - received:\n{result.replace("\x00", "")}")
                for tmp in result.replace("\x00", "").split("\r\n"):
                    if LOG_MATCH in tmp and not re.findall(self.re_start, tmp):
                        count += 1
                        self.log_lines.append(tmp)
                log_file["script_count"] = count
                if log_file["junos_count"] < log_file["junos_count"]:
                    logging.warning(f"file {log_file['file']}: got only {count} entries, expected {log_file['junos_count']}")
                else:
                    logging.debug(f"file {log_file['file']}: got {count} entries, expected {log_file['junos_count']}")


def _load_env(
    env_file: str,
    mist_host: str,
    mist_apitoken: str,
    mist_org_id: str,
    mist_site_id: str,
    mist_device_id: str,
    log_match: str
):
    if env_file.startswith("~/"):
        env_file = os.path.join(os.path.expanduser("~"), env_file.replace("~/", ""))
    load_dotenv(dotenv_path=env_file, override=True)
    if os.getenv("MIST_HOST"):
        mist_host = os.getenv("MIST_HOST")
    if os.getenv("MIST_APITOKEN"):
        mist_apitoken = os.getenv("MIST_APITOKEN")
    if os.getenv("MIST_ORG_ID"):
        mist_org_id = os.getenv("MIST_ORG_ID")
    if os.getenv("MIST_SITE_ID"):
        mist_site_id = os.getenv("MIST_SITE_ID")
    if os.getenv("MIST_DEVICE_ID"):
        mist_device_id = os.getenv("MIST_DEVICE_ID")
    if os.getenv("LOG_MATCH"):
        log_match = os.getenv("LOG_MATCH")
    return mist_host, mist_apitoken, mist_org_id, mist_site_id, mist_device_id, log_match


def get_shell_info():
    url = f"https://{MIST_API_HOST}/api/v1/sites/{MIST_SITE_ID}/devices/{MIST_DEVICE_ID}/shell"
    headers = {"Authorization": f"Token {MIST_APITOKEN}"}
    response = requests.post(url=url, headers=headers, json={})
    if response.status_code == 200:
        data = response.json()
        return data


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        level=logging.DEBUG,
        filename=LOG_FILE,
        filemode="w",
    )
    MIST_HOST, MIST_APITOKEN, MIST_ORG_ID, MIST_SITE_ID, MIST_DEVICE_ID, LOG_MATCH = _load_env(
        ENV_FILE, MIST_HOST, MIST_APITOKEN, MIST_ORG_ID, MIST_SITE_ID, MIST_DEVICE_ID, LOG_MATCH
    )
    MIST_APITOKEN = MIST_APITOKEN.split(",")[0]
    # host for websocket is api-ws.mist.com, so replacing "api." or "manage." with "api-ws." if not the right host
    if MIST_HOST.startswith("api."):
        MIST_API_HOST = MIST_HOST
        MIST_WS_HOST = MIST_HOST.replace("api.", "api-ws.")
    elif MIST_HOST.startswith("manage."):
        MIST_API_HOST = MIST_HOST.replace("manage.", "api.")
        MIST_WS_HOST = MIST_HOST.replace("manage.", "api-ws.")
    print(" SETTINGS ".center(80, "-"))
    print(f"MIST_HOST     : {MIST_HOST}")
    print(f"MIST_APITOKEN : {MIST_APITOKEN[:6]}...{MIST_APITOKEN[-6:]}")
    print(f"MIST_SITE_ID  : {MIST_SITE_ID}")
    print(f"MIST_DEVICE_ID: {MIST_DEVICE_ID}")
    WS_DATA = get_shell_info()
    print(" WS DATA ".center(80, "-"))
    print(WS_DATA)
    print(" STARTING CLI ".center(80, "-"))
    # websocket.enableTrace(True)
    socket = MistSocket(WS_DATA["url"])
    socket.start()
    with open(OUT_FILE, "w") as f:
        f.write("-- statistics --\r\n")
        f.write(f"date: {datetime.now()}\r\n")
        f.write(f"files:\r\n")
        for log_file in socket.log_files:
            f.write(f" - {log_file}\r\n")
        f.write("-- logs --\r\n")
        for line in socket.log_lines:
            f.write(f"{line}\r\n")
