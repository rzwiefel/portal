import uuid
import uuid
import webbrowser
from concurrent.futures import Future
from http.server import BaseHTTPRequestHandler as BRH, ThreadingHTTPServer
from io import StringIO
from threading import Thread
from typing import Any, Dict

from transit.reader import Reader
from transit.transit_types import Keyword as kw, Keyword
from transit.writer import Writer

from Handlers import ObjectValueHandler
import variables as v

current_state = {kw("portal/state-id"): uuid.uuid4(),
                 kw("portal/value"):    []}
deliver = Future()


def pre_req(req: BRH, content_type: str = "text/html", rc: int = 200):
    req.send_response(rc)
    req.send_header("Content-type", content_type)
    req.end_headers()


def send_resource(req: BRH, content_type: str, resource_name: str):
    pre_req(req, content_type=content_type)
    with open(resource_name, "r") as f:
        req.wfile.write(bytes(f.read(), "utf-8"))


def clear_values(arg):
    set_value([])
    v.instance_cache = {}


def set_value(value):
    global deliver
    newval = deliver
    deliver = Future()
    newval.set_result(value)


def log(value: Any):
    val: list = current_state[kw("portal/value")]
    val.insert(0, value)
    set_value(val)


def load_state(args: Dict[Keyword, Any]):
    global current_state
    if args[kw("portal/state-id")] != current_state[kw("portal/state-id")]:
        return current_state
    res = deliver.result()
    current_state = {kw("portal/state-id"): uuid.uuid4(),
                     kw("portal/value"):    res}
    return current_state


def on_nav(args: Dict[Keyword, Any]):
    return {kw("value"): args[kw("args")][-1]}


ops = {kw("portal.rpc/clear-values"): clear_values,
       kw("portal.rpc/load-state"):   load_state,
       kw("portal.rpc/on-nav"):       on_nav}


def rpc(req: BRH):
    reader = Reader("json")
    s = StringIO(str(req.rfile.read(int(req.headers["Content-Length"])), "utf-8"))
    val = reader.read(s)
    f = ops.get(val[kw("op")])
    res = f(val)

    pre_req(req, "application/transit+json; charset=utf-8")

    io = StringIO()
    writer = Writer(io, "json")
    writer.register(object, ObjectValueHandler())
    writer.write(res)
    req.wfile.write(bytes(io.getvalue(), "utf-8"))


def handler(req: BRH):
    {
        "/":        lambda: send_resource(req, "text/html", "../resources/index.html"),
        "/main.js": lambda: send_resource(req, "text/javascript", "../resources/main.js"),
        "/rpc":     lambda: rpc(req)
    }.get(req.path, lambda: pre_req(req, rc=404))()


class Server(BRH):
    def do_POST(self):
        handler(self)

    def do_GET(self):
        handler(self)


def __open_inspector(hostname: str, port: int):
    web_server = ThreadingHTTPServer((hostname, port), Server)
    print(f"Server started http://{hostname}:{port}")
    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped.")


def open_portal(host: str = "localhost", port: int = 8080):
    t = Thread(target=__open_inspector, args=(host, port), daemon=True)
    t.start()
    webbrowser.open("http://localhost:8080")
    return t


if __name__ == "__main__":
    open_portal().join()
