import socket
import struct
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
from pathlib import Path

LOG = Path("superferma_v48_capacity_scale_fix.log")
PRINT_LIMIT = 65535

FIELD_WATER_FULL = 120.0
FRESH_FERTILITY = 120.0
ACTION_SETTLE_SECONDS = 4.0

# Chudo Ferma 2 reference timing copied deliberately for the first crop test.
# We only use values that were directly recovered from its XML; unknown products
# are left untouched instead of guessing.
CHUDO_GROWTH_STAGES = {
    1: (30.0, 30.0, 30.0),  # product_id=1: three growth stages, 90 s total
}

def growth_total_seconds(product_id):
    stages = CHUDO_GROWTH_STAGES.get(int(product_id))
    return sum(stages) if stages else None

def growth_percent(product_id, elapsed_seconds):
    total = growth_total_seconds(product_id)
    if total is None:
        return None
    elapsed = max(0.0, float(elapsed_seconds))
    return min(1.0, elapsed / total)

def refresh_growth_state(state, now=None):
    started = state.get("growth_started_at")
    if started is None:
        return False
    total = growth_total_seconds(state.get("product_id", 0))
    if total is None:
        return False
    if now is None:
        now = time.monotonic()
    new_value = growth_percent(state["product_id"], float(now) - float(started))
    old_value = float(state.get("percent_growth", 0.0))
    state["percent_growth"] = new_value
    return abs(new_value - old_value) > 1e-9


def new_field_state():
    return {
        "status": "grow",
        "water_amount": 0.0,
        "fertil_amount": FRESH_FERTILITY,
        "product_id": 0,
        "percent_growth": 0.0,
        "growth_started_at": None,
    }

def apply_water_state(state):
    state["water_amount"] = FIELD_WATER_FULL

def apply_dig_state(state):
    water = float(state.get("water_amount", 0.0))
    state.update({
        "status": "digged",
        "water_amount": water,
        "fertil_amount": FRESH_FERTILITY,
        "product_id": 0,
        "percent_growth": 0.0,
        "growth_started_at": None,
    })

def heartbeat_growth_allowed(now, last_field_action_at):
    if last_field_action_at is None:
        return True
    return (float(now) - float(last_field_action_at)) >= ACTION_SETTLE_SECONDS


LOGIN_ACCOUNT = bytes.fromhex(
    "313b3b6163746976653b313b313b3132372e302e302e313b3132372e302e302e313b0a783b"
)
ADD_PERSON = bytes.fromhex("310a310a300a")
LOGIN_PERSON = bytes.fromhex(
    "31204c4f43414c4b4559203132372e302e302e3120383836360a"
)

# Exact protobuf payloads generated from the schemas embedded in vf.dll.
#
# GameSettings:
#   32 dense rows in every repeated vocabulary
#   direct IDs = 0..31
#   foreign IDs = 0
#
# UserState:
#   Fogajaro / LocalFarm
#   money=10000
#   stars/crystals/bricks=100
#   all vocabulary references = 0
GAME_SETTINGS = bytes.fromhex("080112002a21080010011d0000803f20012801350000803f3d0000803f40014801500158016001420e0800101418002000280130003800420f080110281896012001280130003800420f0802103c18f4032002280130003800420f0803107818e80720032801300038004210080410c80118d00f20042801300038004a150800100018022500006041286430003801400048004a16080010011804250000404128c80130013802400048004a16080010021806250000204128ac0230023803400048004a16080010031805250000004128900330033804400048004a16080110001802250000604128a00630003804400048004a16080110011804250000404128e80730013802400048004a16080110021806250000204128b00930023803400048004a16080110031805250000004128f80a30033804400048004a16080210001802250000604128ac0230003802400048004a16080210011804250000404128900330013802400048004a16080210021806250000204128f40330023803400048004a16080210031805250000004128d80430033804400048004a16080310001802250000604128b00930003805400048004a16080310011804250000404128f80a30013802400048004a16080310021806250000204128c00c30023803400048004a16080310031805250000004128880e30033804400048004a16080410001802250000904128e80730003805400048004a16080410011804250000804128b00930013802400048004a16080410021806250000404128f80a30023803400048004a16080410031805250000004128c00c30033804400048004a16080510001802250000904128f40330003803400048004a16080510011804250000804128d80430013802400048004a16080510021806250000604128bc0530023803400048004a16080510031805250000404128a00630033804400048004a16080610001802250000904128f80a30003806400048004a16080610011804250000804128c00c30013802400048004a16080610021806250000604128880e30023803400048004a16080610031805250000404128d00f30033804400048004a16080710001802250000604128c80130003802400048004a16080710011804250000404128ac0230013802400048004a16080710021806250000204128900330023803400048004a16080710031805250000004128f40330033804400048004a16080810001802250000604128900330003803400048004a16080810011804250000404128f40330013802400048004a16080810021806250000204128d80430023803400048004a16080810031805250000004128bc0530033804400048004a16080910001802250000604128d80430003804400048004a16080910011804250000404128bc0530013802400048004a16080910021806250000204128a00630023803400048004a16080910031805250000004128840730033804400048004a16080a10001802250000904128c00c30003803400048004a16080a10011804250000804128880e30013802400048004a16080a10021806250000404128d00f30023803400048004a16080a10031805250000204128981130033804400048004a15080b10001802250000f041286430003804400048004a16080b10011804250000204228c80130013802400048004a16080b10021806250000484228c20330023803400048004a16080b10031805250000704228d80430033804400048004a15080c10001802250000f041286430003804400048004a16080c10011804250000204228c80130013802400048004a16080c10021806250000484228c20330023803400048004a16080c10031805250000704228d80430033804400048004a15080d10001802250000f041286430003804400048004a16080d10011804250000204228c80130013802400048004a16080d10021806250000484228c20330023803400048004a16080d10031805250000704228d80430033804400048004a15080e10001802250000f041286430003805400048004a16080e10011804250000204228c80130013802400048004a16080e10021806250000484228c20330023803400048004a16080e10031805250000704228d80430033804400048004a15080f10001802250000f041286430003805400048004a16080f10011804250000204228c80130013802400048004a16080f10021806250000484228c20330023803400048004a16080f10031805250000704228d80430033804400048004a15081010001802250000f041286430003805400048004a16081010011804250000204228c80130013802400048004a16081010021806250000484228c20330023803400048004a16081010031805250000704228d80430033804400048004a15081110001802250000f041286430003805400048004a16081110011804250000204228c80130013802400048004a16081110021806250000484228c20330023803400048004a16081110031805250000704228d80430033804400048004a15081210001802250000f041286430003805400048004a16081210011804250000204228c80130013802400048004a16081210021806250000484228c20330023803400048004a16081210031805250000704228d80430033804400048004a15081310001802250000f041286430003805400048004a16081310011804250000204228c80130013802400048004a16081310021806250000484228c20330023803400048004a16081310031805250000704228d80430033804400048004a15081410001802250000f041286430003805400048004a16081410011804250000204228c80130013802400048004a16081410021806250000484228c20330023803400048004a16081410031805250000704228d80430033804400048004a15081510001802250000f041286430003805400048004a16081510011804250000204228c80130013802400048004a16081510021806250000484228c20330023803400048004a16081510031805250000704228d80430033804400048004a15081610001802250000f041286430003805400048004a16081610011804250000204228c80130013802400048004a16081610021806250000484228c20330023803400048004a16081610031805250000704228d80430033804400048004a15081710001802250000f041286430003805400048004a16081710011804250000204228c80130013802400048004a16081710021806250000484228c20330023803400048004a16081710031805250000704228d80430033804400048004a15081810001802250000f041286430003805400048004a16081810011804250000204228c80130013802400048004a16081810021806250000484228c20330023803400048004a16081810031805250000704228d804300338044000480050ac025a0a080010001801200028005a0b080110f4031803200028005a0b080210fa011802200028005a0b080310e8071803200028005a0b080410c4131805200028005a0b080510de021802200028005a0b080610dc0b1804200028005a0b080710b8171805200028005a0b080810d00f180420002800720e0800100118322001280030003800720e0801100218642002280030003800720f0802100318c80120022800300038007d0000803f85010000803f8801019a010c0800100a18002001280030009a010c0801101418002002280030009a010c0802101e1800200228003000a00101a80101b00101b80101c5010000803fcd010000803ff80101920211687474703a2f2f3132372e302e302e312f980201e00201e80201f00201f80201900301980301a00301a80301b80301c00301d80301e00301e80301f00301f80301800401880401900401980401a00401a80401b00401b80401d80401e00401e80401f00401f8040185050000803f880501")
USER_STATE = bytes.fromhex("08011200180030008001008d010000803f980100a20108466f67616a61726faa01014db2010131ba0100c201094c6f63616c4661726dc80100d00100d80100e00164800200880200900200980200a00200a80200b00200b80200c00200c80200d00200d80264e00264e80200f00200f80200800300900300a00300a80300b00300c20300ca0300d20300d80300e003002064f00100f801002a05087810ca023a160801100018ffffffffffffffffff012205085c10e80242170802100020ffffffffffffffffff013206089b0110e802")

def log(msg=""):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def redact(text):
    out = []
    for p in text.split("&"):
        if p.lower().startswith(("password=", "new_password=")):
            out.append(p.split("=", 1)[0] + "=***")
        else:
            out.append(p)
    return "&".join(out)

def read_varint(data, pos):
    value = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        value |= (b & 0x7f) << shift
        if not (b & 0x80):
            return value, pos
        shift += 7
    raise ValueError("truncated varint")

def parse_proto(data):
    out = []
    pos = 0
    try:
        while pos < len(data):
            key, pos = read_varint(data, pos)
            field, wire = key >> 3, key & 7

            if wire == 0:
                v, pos = read_varint(data, pos)
                out.append((field, wire, v))
            elif wire == 1:
                raw = data[pos:pos+8]
                pos += 8
                out.append((field, wire, raw.hex()))
            elif wire == 2:
                n, pos = read_varint(data, pos)
                raw = data[pos:pos+n]
                pos += n
                try:
                    out.append((field, wire, repr(raw.decode("utf-8"))))
                except Exception:
                    out.append((field, wire, raw.hex()))
            elif wire == 5:
                raw = data[pos:pos+4]
                pos += 4
                out.append((field, wire, raw.hex()))
            else:
                out.append(("parse_error", wire, data[pos:].hex()))
                break
    except Exception as e:
        out.append(("parse_error", repr(e), data.hex()))
    return out

def action_from(decoded):
    for x in decoded:
        if isinstance(x, tuple) and len(x) == 3 and x[0] == 3 and x[1] == 0:
            return x[2]
    return None

def enc_varint(n):
    if n < 0:
        n &= (1 << 64) - 1
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)

def fld_varint(field_no, value):
    return enc_varint((field_no << 3) | 0) + enc_varint(value)

def fld_bytes(field_no, payload):
    return enc_varint((field_no << 3) | 2) + enc_varint(len(payload)) + payload

def fld_float32(field_no, value):
    return enc_varint((field_no << 3) | 5) + struct.pack("<f", float(value))

def build_farm_field(field_id, state):
    # common.proto FarmField:
    #   1=id, 2=water_amount, 3=fertil_amount,
    #   4=product_id, 5=percent_growth, 6=status
    return (
        fld_varint(1, field_id) +
        fld_float32(2, state["water_amount"]) +
        fld_float32(3, state.get("fertil_amount", FRESH_FERTILITY)) +
        fld_varint(4, state["product_id"]) +
        fld_float32(5, state["percent_growth"]) +
        fld_bytes(6, state["status"].encode("ascii"))
    )

def response_with_farm_field(field_id, state):
    farm_field = build_farm_field(field_id, state)
    return fld_varint(1, 1) + fld_bytes(3, farm_field)

def send_packet(conn, payload, label):
    # Raw transport frame: used by the initial direct-connect test.
    if len(payload) >= 32768:
        raise RuntimeError("payload unexpectedly exceeds signed-16-bit-safe size")
    frame = len(payload).to_bytes(2, "little") + payload
    conn.sendall(frame)
    log(f"TCP TX {label}: payload={len(payload)} frame={len(frame)}")
    log(f"TCP TX PREFIX={frame[:2].hex()} HEAD={payload[:80].hex()}")

def send_normal_response(conn, protobuf_payload, label):
    # Original server protocol envelope:
    #   2-byte LE length
    #   1-byte packet opcode / route byte
    #   protobuf body
    #
    # Opcode 0 means a normal response and routes the body to the
    # request callback (e.g. onGameInfoResponse / onUserInfoResponse).
    wrapped = b"\x00" + protobuf_payload

    if len(wrapped) >= 32768:
        raise RuntimeError("wrapped payload unexpectedly exceeds signed-16-bit-safe size")

    frame = len(wrapped).to_bytes(2, "little") + wrapped
    conn.sendall(frame)

    log(f"TCP TX {label}: protobuf={len(protobuf_payload)} wrapped={len(wrapped)} frame={len(frame)}")
    log(f"TCP TX PREFIX={frame[:2].hex()} OPCODE=00 BODY_HEAD={protobuf_payload[:80].hex()}")

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        return self.rfile.read(n) if n else b""

    def _reply(self, payload=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)

    def _handle(self):
        body = self._body()
        log(f"HTTP {self.command} {self.path}")
        if body:
            log("  BODY " + redact(body.decode("utf-8", errors="replace")))

        if self.path.startswith("/cgi-bin/check_version.cgi"):
            self._reply(b"", "application/octet-stream")
        elif self.path.startswith("/cgi-bin/login_account.cgi"):
            self._reply(LOGIN_ACCOUNT)
        elif self.path.startswith("/cgi-bin/add_person.cgi"):
            log("*** stable character: Fogajaro / person_id=1 ***")
            self._reply(ADD_PERSON)
        elif self.path.startswith("/cgi-bin/login_person.cgi"):
            self._reply(LOGIN_PERSON)
        elif self.path.startswith("/cgi-bin/register_account.cgi"):
            self._reply(b"1")
        else:
            log("*** NEW HTTP ENDPOINT ***")
            self._reply(b"")

    do_GET = do_POST = do_HEAD = do_PUT = _handle

    def log_message(self, fmt, *args):
        pass

def tcp_client(conn, addr):
    log("")
    log("#" * 78)
    log(f"### TCP CONNECT {addr[0]}:{addr[1]} ###")
    log("#" * 78)

    conn.settimeout(45)
    direct_done = False

    # v46: authoritative per-field state + Chudo-style timed growth for this TCP/game session.
    # Static UserState remains untouched; a full game restart starts clean.
    farm_fields = {}
    seed_packets = {}
    mow_grass_count = 0
    last_mow_at = {}
    last_growth_field_id = None
    last_field_action_at = None

    def field_state(field_id):
        return farm_fields.setdefault(field_id, new_field_state())

    try:
        while True:
            data = conn.recv(65535)
            if not data:
                break

            log(f"TCP RX {len(data)} HEX={data[:PRINT_LIMIT].hex()}")

            if data == b"1" and not direct_done:
                send_packet(conn, b"1", "RAW DIRECT TEST")
                direct_done = True
                continue

            decoded = parse_proto(data)
            action = action_from(decoded)
            log(f"PROTO={decoded!r}")
            log(f"REQUEST ACTION={action!r}")

            if action == 1:
                send_normal_response(conn, GAME_SETTINGS, "GameSettings + 00 envelope")
                log("*** ACTION 1 GameSettings SENT WITH OPCODE 00 (ALL fake-32 tables omitted) ***")
                log("*** no memory patch is used ***")
                continue

            if action == 2:
                send_normal_response(conn, USER_STATE, "UserState + 00 envelope")
                log("*** ACTION 2 UserState SENT WITH NORMAL OPCODE 00 ***")
                log("*** WATCH THE GAME WINDOW ***")
                continue

            if action == 106:
                now = time.monotonic()
                if not heartbeat_growth_allowed(now, last_field_action_at):
                    action106_payload = bytes.fromhex("0801")
                    remaining = ACTION_SETTLE_SECONDS - (now - last_field_action_at)
                    send_normal_response(conn, action106_payload, "Action106 Suppressed During Field Action + 00 envelope")
                    log(f"*** ACTION 106 GROWTH SYNC SUPPRESSED settle_remaining={max(0.0, remaining):.2f}s ***")
                elif last_growth_field_id is not None and last_growth_field_id in farm_fields:
                    state = field_state(last_growth_field_id)
                    refresh_growth_state(state, now=now)
                    action106_payload = response_with_farm_field(last_growth_field_id, state)
                    total = growth_total_seconds(state["product_id"])
                    started = state.get("growth_started_at")
                    elapsed = (now - started) if started is not None else 0.0
                    log(
                        f"*** ACTION 106 GROWTH SYNC field={last_growth_field_id} "
                        f"product={state['product_id']} elapsed={elapsed:.1f}s/"
                        f"{total if total is not None else 'n/a'} "
                        f"percent={state['percent_growth']:.4f} "
                        f"water={state['water_amount']:.3f} fertil={state['fertil_amount']:.3f} ***"
                    )
                    send_normal_response(conn, action106_payload, "Action106 Growth FarmField Response + 00 envelope")
                else:
                    action106_payload = bytes.fromhex("0801")
                    send_normal_response(conn, action106_payload, "Action106 Response + 00 envelope")
                    log("*** ACTION 106 -> Response(result=1) SENT (no timed field yet) ***")
                continue

            if action == 4:
                last_field_action_at = time.monotonic()
                water_payload = bytes.fromhex("0801")
                send_normal_response(conn, water_payload, "Action4 Water Response + 00 envelope")
                log("*** ACTION 4 -> Response(result=1) SENT (water test) ***")
                continue

            if action == 203:
                field_id = None
                for field_no, wire_type, value in decoded:
                    if field_no == 7 and wire_type == 0:
                        field_id = int(value)
                        break

                if field_id is None:
                    water_payload = fld_varint(1, 1)
                    log("*** ACTION 203: field_id missing; falling back to result=1 ***")
                else:
                    state = field_state(field_id)
                    refresh_growth_state(state)
                    before = dict(state)
                    apply_water_state(state)
                    last_field_action_at = time.monotonic()
                    water_payload = response_with_farm_field(field_id, state)
                    log(
                        f"*** ACTION 203: field={field_id} WATER "
                        f"before={before} after={state} ***"
                    )

                send_normal_response(
                    conn,
                    water_payload,
                    "Action203 Stateful Water FarmField Response + 00 envelope"
                )
                log("*** ACTION 203 -> full FarmField with water_amount=120.0 SENT ***")
                continue

            if action == 201:
                field_id = None
                for field_no, wire_type, value in decoded:
                    if field_no == 7 and wire_type == 0:
                        field_id = int(value)
                        break

                if field_id is None:
                    dig_payload = fld_varint(1, 1)
                    log("*** ACTION 201: field_id missing; falling back to result=1 ***")
                else:
                    state = field_state(field_id)
                    before = dict(state)
                    # Freshly dug soil restores fertility and preserves moisture.
                    apply_dig_state(state)
                    last_field_action_at = time.monotonic()
                    last_mow_at.pop(field_id, None)
                    if last_growth_field_id == field_id:
                        last_growth_field_id = None
                    dig_payload = response_with_farm_field(field_id, state)
                    log(
                        f"*** ACTION 201: field={field_id} DIG "
                        f"before={before} after={state} ***"
                    )

                send_normal_response(
                    conn,
                    dig_payload,
                    "Action201 Stateful Dig FarmField Response + 00 envelope"
                )
                log("*** ACTION 201 -> fresh fertile FarmField(status=digged); water preserved ***")
                continue

            if action == 202:
                field_id = None
                mow_machine_id = None
                for field_no, wire_type, value in decoded:
                    if field_no == 7 and wire_type == 0:
                        field_id = int(value)
                    elif field_no == 9 and wire_type == 0:
                        mow_machine_id = int(value)

                if field_id is None:
                    mow_payload = fld_varint(1, 1)
                    log("*** ACTION 202: field_id missing; falling back to result=1 ***")
                else:
                    state = field_state(field_id)
                    refresh_growth_state(state)
                    before = dict(state)

                    # Harvest must NOT turn the field into a dug/empty cell.
                    # Preserve product_id and water. For product_id=1, restart
                    # the Chudo Ferma 2 reference growth timer: 30+30+30 s.
                    now = time.monotonic()
                    last_field_action_at = now
                    prev_mow = last_mow_at.get(field_id)
                    duplicate = prev_mow is not None and (now - prev_mow) < 1.0
                    if not duplicate:
                        state["status"] = "grow"
                        state["percent_growth"] = 0.0
                        if growth_total_seconds(state["product_id"]) is not None:
                            state["growth_started_at"] = now
                            last_growth_field_id = field_id
                        mow_grass_count += 1
                        last_mow_at[field_id] = now
                    else:
                        refresh_growth_state(state, now=now)

                    farm_field = build_farm_field(field_id, state)
                    mow_product = (
                        fld_varint(1, 0) +
                        fld_varint(2, mow_grass_count)
                    )

                    mm_id = mow_machine_id if mow_machine_id is not None else 2
                    mow_machine = (
                        fld_varint(1, mm_id) +
                        fld_varint(2, 0) +
                        fld_bytes(5, mow_product)
                    )

                    mow_payload = (
                        fld_varint(1, 1) +
                        fld_bytes(3, farm_field) +
                        fld_bytes(6, mow_machine)
                    )

                    log(
                        f"*** ACTION 202: field={field_id} MOW mower={mm_id} "
                        f"duplicate={duplicate} grass_count={mow_grass_count} "
                        f"before={before} after={state} ***"
                    )

                send_normal_response(
                    conn,
                    mow_payload,
                    "Action202 Stateful Mow FarmField+MowMachine Response + 00 envelope"
                )
                log("*** ACTION 202 -> plant preserved; growth reset; mower updated ***")
                continue

            if action == 204:
                field_id = None
                seed_packet_id = None
                for field_no, wire_type, value in decoded:
                    if field_no == 7 and wire_type == 0:
                        field_id = int(value)
                    elif field_no == 12 and wire_type == 0:
                        seed_packet_id = int(value)

                if field_id is None:
                    sow_payload = fld_varint(1, 1)
                    log("*** ACTION 204: field_id missing; falling back to result=1 ***")
                else:
                    state = field_state(field_id)
                    before = dict(state)
                    product_id = seed_packets.get(seed_packet_id, 0)
                    state["status"] = "grow"
                    state["product_id"] = product_id
                    last_field_action_at = time.monotonic()
                    state["percent_growth"] = 0.0
                    state["growth_started_at"] = (
                        time.monotonic()
                        if growth_total_seconds(product_id) is not None
                        else None
                    )
                    if state["growth_started_at"] is not None:
                        last_growth_field_id = field_id
                    last_mow_at.pop(field_id, None)
                    sow_payload = response_with_farm_field(field_id, state)
                    log(
                        f"*** ACTION 204: field={field_id} SOW seed_packet={seed_packet_id} "
                        f"product_id={product_id} before={before} after={state} ***"
                    )

                send_normal_response(
                    conn,
                    sow_payload,
                    "Action204 Stateful Sow FarmField Response + 00 envelope"
                )
                log("*** ACTION 204 -> full FarmField(status=grow) SENT ***")
                continue

            if action == 7:
                action7_payload = bytes.fromhex("0801")
                send_normal_response(conn, action7_payload, "Action7 Response + 00 envelope")
                log("*** ACTION 7 -> Response(result=1) SENT (market transition test) ***")
                continue

            if action == 5:
                product_id = None
                for field_no, wire_type, value in decoded:
                    if field_no == 11 and wire_type == 0:
                        product_id = int(value)
                        break

                # Keep the already-working response id=1, but remember its product.
                if product_id is not None:
                    seed_packets[1] = product_id
                buy_seed_payload = fld_varint(1, 1) + fld_varint(5, 1)
                send_normal_response(
                    conn,
                    buy_seed_payload,
                    "Action5 BuySeed Response + seed_packet_id + 00 envelope"
                )
                log(
                    f"*** ACTION 5 -> seed_packet_id=1 mapped to product_id={product_id}; "
                    f"seed_packets={seed_packets} ***"
                )
                continue

            log("")
            log("!" * 78)
            log("*** UNKNOWN ACTION -> TEST SUCCESS FALLBACK ***")
            log(f"*** ACTION={action!r} ***")
            log("!" * 78)

            fallback_payload = bytes.fromhex("0801")
            send_normal_response(
                conn,
                fallback_payload,
                f"Action{action} Generic Response + 00 envelope"
            )
            log(f"*** ACTION {action!r} -> Response(result=1) SENT (GENERIC TEST FALLBACK) ***")
            continue

    except socket.timeout:
        log("TCP timeout")
    except Exception as e:
        log(f"TCP error: {e!r}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        log("TCP DISCONNECT")

def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 8866))
    s.listen(30)
    log("TCP v48-capacity-scale-fix listening on 127.0.0.1:8866")

    while True:
        c, a = s.accept()
        threading.Thread(target=tcp_client, args=(c, a), daemon=True).start()

def http_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    log("HTTP v48-capacity-scale-fix listening on 127.0.0.1:8080")
    srv.serve_forever()

if __name__ == "__main__":
    print("Superferma local server v48-capacity-scale-fix")
    print("----------------------------------------------")
    print("IMPORTANT:")
    print("  NO memory patches or probes for this test.")
    print("  Restart game.exe before testing v48.")
    print("")
    print("GameSettings payload:", len(GAME_SETTINGS), "bytes")
    print("UserState payload:", len(USER_STATE), "bytes")
    print("")
    print("Protocol fix:")
    print("  normal server response = 00 + protobuf")
    print("  frame length includes that leading 00 byte")
    print("")
    print("Current GameSettings fixes retained:")
    print("  hotbed_voc -> only id=0")
    print("  depot_voc  -> exact Game.xml grid: 25 types x 4 levels")
    print("  depot_field_voc -> slots 0..8 only (id=9 omitted for A/B test)")
    print("  spade_voc -> OMITTED (client local config retained)")
    print("  mow_machine_voc -> OMITTED (client local config retained)")
    print("  ALL remaining fake 32-row vocab tables -> OMITTED")
    print("  ACTION 106 -> Response(result=1)")
    print("  UserState money -> 100")
    print("  UserState spade -> id=1 type=0 resource_left=-1")
    print("  UserState mow_machine -> id=2 type=0 resource_left=-1")
    print("  max_spade_level_id/max_mow_level_id -> 0")
    print("  ACTION 4 -> Response(result=1) [water test]")
    print("  ACTION 203 -> full FarmField, water=120.0, fertility/crop state preserved")
    print("  farmer_position -> (120, 330)")
    print("  spade_position -> (92, 360)")
    print("  mow_position -> (155, 360)")
    print("  character id is fixed: Fogajaro / person_id=1")
    print('  ACTION 201 -> fresh fertile digged field; water preserved; product cleared')
    print("  grass_to_start_grow -> 300 [diagnostic timer test]")
    print('  ACTION 202 -> FarmField(status="grow", preserved water/product, growth=0) + MowMachine')
    print("  market_counter_voc -> 3 real/minimal rows from CounterUpInfo")
    print("  market_shelf_type_voc -> 3 real/minimal rows from ShelfCapacity")
    print("  ACTION 7 -> Response(result=1) [market transition test]")
    print("  ACTION 5 -> seed_packet_id=1 + server mapping to requested product_id")
    print("  ACTION 204 -> full FarmField(status=grow), planted product remembered")
    print("  ALL unknown ACTIONs -> Response(result=1) [diagnostic fallback]")
    print("  warehouse_voc -> 5 real client levels")
    print("  EXPERIMENT: product_id=1 growth -> 30+30+30 sec (90 sec total)")
    print("  ACTION 204/ACTION 202 start that timer and keep product_id")
    print("  ACTION 106 growth sync suppressed for 4s after field actions")
    print("  FarmField field3 fertil_amount -> explicit; fresh dig = 120.0")
    print("  ACTION 201 preserves water_amount")
    print("  CAPACITY SCALE FIX: full water=120.0; fresh fertility=120.0")
    print("")
    print("Expected startup:")
    print("  ACTION 1 -> 00 + GameSettings")
    print("  client parses GameSettings and sends ACTION 2")
    print("  ACTION 2 -> 00 + UserState")
    print("")
    print("Watch both the console and game window.")
    print("Send superferma_v48_capacity_scale_fix.log + screenshot after the test.")
    print("")

    threading.Thread(target=http_server, daemon=True).start()
    tcp_server()
