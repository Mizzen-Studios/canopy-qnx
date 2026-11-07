#!/usr/bin/env python3
"""Offline receipt recheck only; never a fresh native/SSH/SocketCAN claim."""
import json
from pathlib import Path
import sys
from native_can_three import require_exact
def verify(folder):
    root=Path(folder);report=json.loads((root/"receipt.json").read_text())
    if report.get("success") is not True or report.get("guest_stopped_reaped") is not True:
        raise ValueError("failed or unreaped native run")
    caps=report["caps"];q,p=map(int,caps["cpu.max"].split())
    if not 0<q<=p or not 0<int(caps["memory.max"])<=1073741824 or caps["nice"]<15:
        raise ValueError("invalid effective caps")
    if "observed in this QEMU run" not in report["label"]:raise ValueError("missing observation qualifier")
    rows=report["restarts"]
    if len(rows)!=3:raise ValueError("require three restarts")
    previous=None;main=report["main_io_sock_pid"]
    for number,row in enumerate(rows,1):
        if row["run"]!=number or row["killed_pid"]==row["new_pid"] or main in (row["killed_pid"],row["new_pid"]) or row["main_pid_unchanged"] is not True:
            raise ValueError("unsafe or missing process transition")
        if previous is not None and row["killed_pid"]!=previous:raise ValueError("broken managed process chain")
        previous=row["new_pid"]
        data=json.loads((root/("traffic"+str(number)+".json")).read_text())
        if data["run"]!=number:raise ValueError("wrong traffic run")
        require_exact(data["host_rx"],data["qnx_rx"])
        require_exact(data["native_tx_expected"],data["host_tx"])
        if row["traffic"]!={"rx_host":100,"rx_qnx":100,"tx_expected":100,"tx_host":100,"ordered_byte_exact":True}:raise ValueError("wrong observed counts")
    return report
if __name__=="__main__":
    verify(sys.argv[1]);print("PASS: offline three-restart RX100/TX100 byte-exact libcan evidence; NOT a fresh run or SSH/SocketCAN acceptance")
