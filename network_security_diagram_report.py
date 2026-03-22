#!/usr/bin/env python3
"""Generate a network diagram, risk summaries, and a PDF report from PPSM CSV data."""

from __future__ import annotations

import csv
import argparse
import re
import subprocess
import shutil
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from diagrams import Cluster, Diagram, Edge
from diagrams.generic.compute import Rack
from fpdf import FPDF

try:
    import vsdx
    from vsdx import Media
except ImportError:
    vsdx = None
    Media = None

# Known high-risk ports. Matching ports are always treated as HIGH severity.
DANGER_PORTS: Dict[int, str] = {
    21: "FTP",
    23: "Telnet",
    3389: "RDP",
    445: "SMB/CIFS",
    139: "NetBIOS Session",
    5900: "VNC",
    1433: "MSSQL",
}

MEDIUM_RISK_PORTS = {22, 25, 53, 110, 135, 137, 138, 161, 389, 587, 993, 995}
HIGH_RISK_SERVICE_WORDS = {"telnet", "ftp", "rdp", "msrdp", "vnc"}
MEDIUM_RISK_SERVICE_WORDS = {"smb", "cifs", "dce-rpc", "netbios", "epmap", "isakmp"}


@dataclass
class Connection:
    from_device: str
    to_device: str
    operating_system: str
    ip_address: str
    mac_address: str
    low_port: Optional[int]
    protocol: str
    service: str
    boundaries: List[str]
    boundary_group: str
    severity: str
    vulnerability_score: str
    danger_reason: str
    unknown_service: bool


def normalize(value: str) -> str:
    return (value or "").strip()


def to_port(value: str) -> Optional[int]:
    value = normalize(value)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def is_unknown_service(service: str) -> bool:
    lower = service.lower()
    return "?" in service or lower == "unknown" or "unknown" in lower


def evaluate_risk(low_port: Optional[int], service: str) -> Tuple[str, str, str]:
    """Return (severity, score, reason)."""
    service_lower = service.lower()

    if low_port in DANGER_PORTS:
        reason = f"Danger port {low_port}/{DANGER_PORTS[low_port]}"
        return "HIGH", "High", reason

    if any(word in service_lower for word in HIGH_RISK_SERVICE_WORDS):
        return "HIGH", "High", "High-risk service keyword"

    if low_port in MEDIUM_RISK_PORTS:
        return "MEDIUM", "Medium", "Medium-risk port"

    if any(word in service_lower for word in MEDIUM_RISK_SERVICE_WORDS):
        return "MEDIUM", "Medium", "Medium-risk service keyword"

    if low_port is not None and low_port < 1024:
        return "MEDIUM", "Medium", "Privileged port range"

    return "LOW", "Low", "No high-risk indicators"


def primary_boundary(counter: Counter) -> str:
    if not counter:
        return "Unassigned"
    # Pick the most frequent boundary for deterministic cluster placement.
    return counter.most_common(1)[0][0]


def parse_csv(
    csv_path: Path,
) -> Tuple[List[Connection], Dict[str, str], Dict[str, str], Dict[str, str], datetime]:
    parsed_at = datetime.now()
    connections: List[Connection] = []
    device_os: Dict[str, str] = {}
    device_ip: Dict[str, str] = {}
    device_mac: Dict[str, str] = {}
    device_boundary_counter: Dict[str, Counter] = defaultdict(Counter)

    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV appears empty or missing headers.")

        boundary_cols = [name for name in reader.fieldnames if name.lower().startswith("boundary")]

        raw_rows = []
        for row in reader:
            from_device = normalize(row.get("FromDevice", ""))
            to_device = normalize(row.get("ToDevice", ""))
            operating_system = normalize(row.get("OperatingSystem", "Unknown OS")) or "Unknown OS"
            ip_address = normalize(row.get("IPAddress", ""))
            mac_address = normalize(row.get("MACAddress", ""))

            if not from_device or not to_device:
                continue

            low_port = to_port(row.get("Low Port", ""))
            protocol = normalize(row.get("Protocol", "")).upper() or "UNK"
            service = normalize(row.get("Service", "")) or "unknown"
            active_boundaries = [b for b in boundary_cols if normalize(row.get(b, "")).upper() == "X"]

            device_os[from_device] = operating_system
            device_os.setdefault(to_device, "Unknown OS")
            if ip_address:
                device_ip[from_device] = ip_address
            if mac_address:
                device_mac[from_device] = mac_address

            device_ip.setdefault(to_device, "")
            device_mac.setdefault(to_device, "")

            for boundary in active_boundaries:
                device_boundary_counter[from_device][boundary] += 1
                device_boundary_counter[to_device][boundary] += 1

            raw_rows.append(
                {
                    "from_device": from_device,
                    "to_device": to_device,
                    "operating_system": operating_system,
                    "ip_address": ip_address,
                    "mac_address": mac_address,
                    "low_port": low_port,
                    "protocol": protocol,
                    "service": service,
                    "boundaries": active_boundaries,
                }
            )

    # Ensure every device has deterministic identity data, even if it never appears as FromDevice.
    all_devices = set(list(device_os.keys()) + list(device_ip.keys()) + list(device_mac.keys()))
    used_octets = {
        int(ip.split(".")[-1])
        for ip in device_ip.values()
        if ip.startswith("192.168.30.") and ip.split(".")[-1].isdigit()
    }
    next_octet = 10
    for device in sorted(all_devices):
        if not device_ip.get(device):
            while next_octet in used_octets and next_octet <= 254:
                next_octet += 1
            if next_octet <= 254:
                device_ip[device] = f"192.168.30.{next_octet}"
                used_octets.add(next_octet)
        if not device_mac.get(device):
            octet = device_ip.get(device, "").split(".")[-1]
            if octet.isdigit():
                device_mac[device] = f"02:30:00:00:00:{int(octet):02x}"
            else:
                device_mac[device] = "Unknown"

    boundary_map = {
        device: primary_boundary(device_boundary_counter.get(device, Counter()))
        for device in all_devices
    }

    for row in raw_rows:
        severity, score, reason = evaluate_risk(row["low_port"], row["service"])
        unknown_flag = is_unknown_service(row["service"])
        group = boundary_map.get(row["from_device"], "Unassigned")
        connections.append(
            Connection(
                from_device=row["from_device"],
                to_device=row["to_device"],
                operating_system=row["operating_system"],
                ip_address=row["ip_address"] or device_ip.get(row["from_device"], "Unknown"),
                mac_address=row["mac_address"] or device_mac.get(row["from_device"], "Unknown"),
                low_port=row["low_port"],
                protocol=row["protocol"],
                service=row["service"],
                boundaries=row["boundaries"],
                boundary_group=group,
                severity=severity,
                vulnerability_score=score,
                danger_reason=reason,
                unknown_service=unknown_flag,
            )
        )

    return connections, device_os, device_ip, device_mac, parsed_at


def style_for_connection(connection: Connection) -> Dict[str, str]:
    if connection.severity == "HIGH":
        return {
            "color": "red",
            "style": "bold",
            "penwidth": "3.5",
            "fontcolor": "red",
            "fontsize": "30",
        }
    if connection.severity == "MEDIUM":
        return {
            "color": "darkorange",
            "style": "solid",
            "penwidth": "2.2",
            "fontcolor": "darkorange",
            "fontsize": "30",
        }

    return {
        "color": "royalblue",
        "style": "solid",
        "penwidth": "1.1",
        "fontcolor": "royalblue",
        "fontsize": "30",
    }


def build_diagram(
    output_prefix: Path,
    connections: List[Connection],
    device_os: Dict[str, str],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
) -> Path:
    all_devices = sorted(device_os.keys())
    device_groups: Dict[str, List[str]] = defaultdict(list)
    for connection in connections:
        device_groups[connection.boundary_group].append(connection.from_device)
        device_groups[connection.boundary_group].append(connection.to_device)

    unique_group_devices = {
        group: sorted(set(devices)) for group, devices in device_groups.items() if devices
    }

    for device in all_devices:
        in_group = any(device in group_devices for group_devices in unique_group_devices.values())
        if not in_group:
            unique_group_devices.setdefault("Unassigned", []).append(device)

    graph_attr = {
        # 10in * 200dpi = 2000px exact square output.
        "dpi": "200",
        "rankdir": "LR",
        "size": "10,10!",
        "ratio": "fill",
        "splines": "spline",
        "overlap": "false",
        "concentrate": "true",
        "nodesep": "0.05",
        "ranksep": "0.08",
        "pad": "0.02",
        "margin": "0.0",
        "fontsize": "36",
        "labelloc": "t",
        "pack": "true",
        "packmode": "node",
    }
    node_attr = {
        "fontsize": "34",
        "labelloc": "b",
        "imagepos": "tc",
    }
    edge_attr = {"fontsize": "28"}

    nodes = {}
    with Diagram(
        "OpenRMF Professional Generated Network Security Diagram",
        filename=str(output_prefix),
        outformat="png",
        show=False,
        direction="LR",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        for group_name in sorted(unique_group_devices.keys()):
            with Cluster(f"Subnet/VLAN: {group_name}"):
                for device in sorted(set(unique_group_devices[group_name])):
                    ip = device_ip.get(device, "Unknown")
                    mac = device_mac.get(device, "Unknown")
                    nodes[device] = Rack(
                        f"Server: {device}\nIP: {ip}\nMAC: {mac}",
                        fontsize="34",
                        labelloc="b",
                        imagepos="tc",
                    )

        for connection in connections:
            port_text = str(connection.low_port) if connection.low_port is not None else "N/A"
            edge_label = f"{port_text}/{connection.protocol} {connection.service}"
            edge_style = style_for_connection(connection)

            # Unknown/questionable services are highlighted in yellow text.
            if connection.unknown_service:
                edge_style["fontcolor"] = "goldenrod"

            src = nodes.get(connection.from_device)
            dst = nodes.get(connection.to_device)
            if src and dst:
                src >> Edge(label=edge_label, **edge_style) >> dst

    diagram_path = output_prefix.with_suffix(".png")

    # Force exact 2000x2000 output on macOS for consistent downstream use.
    if diagram_path.exists():
        try:
            subprocess.run(["sips", "-z", "2000", "2000", str(diagram_path)], check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    return diagram_path


def _mermaid_id(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not safe:
        safe = "node"
    if safe[0].isdigit():
        safe = f"n_{safe}"
    return safe


def _mermaid_text(value: str) -> str:
    return (value or "").replace('"', "'").replace("|", "/")


def write_mermaid_diagram(
    output_dir: Path,
    connections: List[Connection],
    device_os: Dict[str, str],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
) -> Path:
    """Write a Mermaid flowchart file that can be rendered in browser or markdown viewers."""
    mermaid_path = output_dir / "soteria_network_diagram.mmd"

    all_devices = sorted(device_os.keys())
    device_group_counter: Dict[str, Counter] = defaultdict(Counter)
    for connection in connections:
        device_group_counter[connection.from_device][connection.boundary_group] += 1
        device_group_counter[connection.to_device][connection.boundary_group] += 1

    unique_group_devices: Dict[str, List[str]] = defaultdict(list)
    for device in all_devices:
        group = primary_boundary(device_group_counter.get(device, Counter()))
        unique_group_devices[group].append(device)

    lines: List[str] = [
        "flowchart LR",
        "  %% Auto-generated Mermaid network diagram",
    ]

    for group_name in sorted(unique_group_devices.keys()):
        group_id = _mermaid_id(group_name)
        lines.append(f"  subgraph {group_id}[\"Subnet/VLAN: {_mermaid_text(group_name)}\"]")
        for device in sorted(set(unique_group_devices[group_name])):
            node_id = _mermaid_id(device)
            label = (
                f"Server: {_mermaid_text(device)}<br/>"
                f"IP: {_mermaid_text(device_ip.get(device, 'Unknown'))}<br/>"
                f"MAC: {_mermaid_text(device_mac.get(device, 'Unknown'))}"
            )
            lines.append(f"    {node_id}[\"{label}\"]")
        lines.append("  end")

    seen_edges = set()
    for connection in connections:
        src = _mermaid_id(connection.from_device)
        dst = _mermaid_id(connection.to_device)
        port_text = str(connection.low_port) if connection.low_port is not None else "N/A"
        edge_label = _mermaid_text(f"{port_text}/{connection.protocol} {connection.service}")
        edge_key = (src, dst, edge_label)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        lines.append(f"  {src} -->|\"{edge_label}\"| {dst}")

    mermaid_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mermaid_path


def write_visio_diagram(
    output_dir: Path,
    connections: List[Connection],
    device_os: Dict[str, str],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
    *,
    include_edges: bool = True,
    output_filename: str = "soteria_network_diagram.vsdx",
    remove_seed_shapes: bool = True,
) -> Path:
    """Write an open-source .vsdx network diagram using the vsdx package."""
    if vsdx is None:
        raise RuntimeError(
            "Missing optional dependency 'vsdx'. Install it with: pip install vsdx"
        )

    visio_path = output_dir / output_filename
    media_path = Path(vsdx.__file__).resolve().parent / "media" / "media.vsdx"
    shutil.copyfile(media_path, visio_path)

    all_devices = sorted(device_os.keys())
    device_group_counter: Dict[str, Counter] = defaultdict(Counter)
    for connection in connections:
        device_group_counter[connection.from_device][connection.boundary_group] += 1
        device_group_counter[connection.to_device][connection.boundary_group] += 1

    grouped_devices: Dict[str, List[str]] = defaultdict(list)
    for device in all_devices:
        group = primary_boundary(device_group_counter.get(device, Counter()))
        grouped_devices[group].append(device)

    # Visio coordinates are in inches from page origin.
    left_margin = 1.6
    top_y = 9.6
    group_x_gap = 3.8
    row_y_gap = 1.45
    node_w = 2.7
    node_h = 1.05
    header_h = 0.55

    with vsdx.VisioFile(str(visio_path)) as vis:
        page = vis.pages[0]
        page.name = "Network Diagram"

        # Clone only from template shapes that already exist in this page.
        rect_master = page.find_shape_by_text("RECTANGLE")
        line_master = page.find_shape_by_text("LINE")
        if rect_master is None or line_master is None:
            raise RuntimeError("Template shapes RECTANGLE/LINE not found in base VSDX page.")

        device_shapes = {}

        for group_index, group_name in enumerate(sorted(grouped_devices.keys())):
            group_x = left_margin + (group_index * group_x_gap)

            header = rect_master.copy(page)
            header.width = node_w
            header.height = header_h
            header.x = group_x
            header.y = top_y + 0.8
            header.text = f"Subnet/VLAN: {group_name}"

            for row_index, device in enumerate(sorted(set(grouped_devices[group_name]))):
                node = rect_master.copy(page)
                node.width = node_w
                node.height = node_h
                node.x = group_x
                node.y = top_y - (row_index * row_y_gap)
                node.text = (
                    f"{device}\n"
                    f"IP: {device_ip.get(device, 'Unknown')}\n"
                    f"MAC: {device_mac.get(device, 'Unknown')}\n"
                    f"OS: {device_os.get(device, 'Unknown OS')}"
                )
                device_shapes[device] = node

        if include_edges:
            seen_edges = set()
            for connection in connections:
                src = device_shapes.get(connection.from_device)
                dst = device_shapes.get(connection.to_device)
                if not src or not dst:
                    continue

                port_text = str(connection.low_port) if connection.low_port is not None else "N/A"
                edge_label = f"{port_text}/{connection.protocol} {connection.service}"
                edge_key = (connection.from_device, connection.to_device, edge_label)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)

                edge = line_master.copy(page)
                src_x, src_y = src.center_x_y
                dst_x, dst_y = dst.center_x_y
                edge.begin_x = src_x
                edge.begin_y = src_y
                edge.end_x = dst_x
                edge.end_y = dst_y
                edge.x = src_x
                edge.y = src_y
                edge.width = dst_x - src_x
                edge.height = dst_y - src_y
                edge.text = edge_label

                # Best-effort edge severity styling. Keep diagram generation resilient.
                try:
                    if connection.severity == "HIGH":
                        edge.set_cell_formula("LineColor", "RGB(255,0,0)")
                        edge.set_cell_value("LineWeight", "0.035 in")
                    elif connection.severity == "MEDIUM":
                        edge.set_cell_formula("LineColor", "RGB(255,140,0)")
                        edge.set_cell_value("LineWeight", "0.02 in")
                    else:
                        edge.set_cell_formula("LineColor", "RGB(65,105,225)")
                        edge.set_cell_value("LineWeight", "0.014 in")
                except Exception:
                    pass

        # Optionally remove original seed/template shapes from the base media file.
        if remove_seed_shapes:
            for seed_text in ["RECTANGLE", "CONNECTED_SHAPE", "STRAIGHT_CONNECTOR", "CURVED_CONNECTOR", "CIRCLE", "LINE"]:
                seed = page.find_shape_by_text(seed_text)
                if seed is not None:
                    seed.remove()

        # Drop stale Connect rows that still reference deleted shapes.
        ns = "{http://schemas.microsoft.com/office/visio/2012/main}"
        shape_ids = {
            s.attrib.get("ID")
            for s in page.xml.findall(f".//{ns}Shape")
            if s.attrib.get("ID")
        }
        connects_parent = page.xml.find(f".//{ns}Connects")
        if connects_parent is not None:
            for connect in list(connects_parent.findall(f"{ns}Connect")):
                from_id = connect.attrib.get("FromSheet")
                to_id = connect.attrib.get("ToSheet")
                if from_id not in shape_ids or to_id not in shape_ids:
                    connects_parent.remove(connect)

            # If all connects were removed, drop the empty container as well.
            if not list(connects_parent):
                root = page.xml.getroot()
                root.remove(connects_parent)

        vis.save_vsdx(str(visio_path))

    return visio_path


def write_visio_mydraw_ultra_safe(
    output_dir: Path,
    connections: List[Connection],
    device_os: Dict[str, str],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
) -> Path:
    """Write a minimal-risk VSDX by raw editing smoke-template text only.

    This intentionally avoids the vsdx serializer because MyDraw is strict about
    the original XML namespace/prefix formatting of the template file.
    """
    if vsdx is None:
        raise RuntimeError(
            "Missing optional dependency 'vsdx'. Install it with: pip install vsdx"
        )

    visio_path = output_dir / "soteria_network_diagram_mydraw_ultra_safe.vsdx"
    media_path = Path(vsdx.__file__).resolve().parent / "media" / "media.vsdx"
    tmp_path = output_dir / "soteria_network_diagram_mydraw_ultra_safe.tmp.vsdx"

    devices = sorted(device_os.keys())
    device_lines = [
        f"{d} | {device_ip.get(d, 'Unknown')} | {device_mac.get(d, 'Unknown')} | {device_os.get(d, 'Unknown OS')}"
        for d in devices[:8]
    ]
    conn_lines = [
        f"{c.from_device}->{c.to_device} {c.low_port if c.low_port is not None else 'N/A'}/{c.protocol} {c.service} [{c.severity}]"
        for c in connections[:12]
    ]

    # Escape XML content but preserve line breaks for readability.
    def xml_escape(value: str) -> str:
        return (
            (value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    replacements = {
        "RECTANGLE\n": "Devices\n" + "\n".join(device_lines),
        "CONNECTED_SHAPE\n": "Connections\n" + "\n".join(conn_lines),
        "CIRCLE\n": f"Totals\nDevices: {len(devices)}\nConnections: {len(connections)}",
        "LINE\n": "Generated by python-network-diagram",
    }

    with zipfile.ZipFile(media_path, "r") as zin, zipfile.ZipFile(tmp_path, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "visio/pages/page1.xml":
                text = data.decode("utf-8")
                for old_text, new_text in replacements.items():
                    old_fragment = f">{xml_escape(old_text)}<"
                    new_fragment = f">{xml_escape(new_text)}<"
                    text = text.replace(old_fragment, new_fragment, 1)
                data = text.encode("utf-8")
            zout.writestr(info, data)

    tmp_path.replace(visio_path)

    return visio_path


def write_summary_tables(
    output_dir: Path,
    connections: List[Connection],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
) -> Tuple[Path, Path]:
    high_risk_path = output_dir / "high_risk_summary.csv"
    full_summary_path = output_dir / "all_connections_summary.csv"

    with high_risk_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "FromDevice",
                "ToDevice",
                "IPAddress",
                "MACAddress",
                "ToIPAddress",
                "ToMACAddress",
                "Low Port",
                "Protocol",
                "Service",
                "Severity",
                "Vulnerability Score",
                "Boundary Group",
                "Reason",
            ]
        )
        for connection in connections:
            if connection.severity != "HIGH":
                continue
            writer.writerow(
                [
                    connection.from_device,
                    connection.to_device,
                    connection.ip_address,
                    connection.mac_address,
                    device_ip.get(connection.to_device, "Unknown"),
                    device_mac.get(connection.to_device, "Unknown"),
                    connection.low_port if connection.low_port is not None else "N/A",
                    connection.protocol,
                    connection.service,
                    connection.severity,
                    connection.vulnerability_score,
                    connection.boundary_group,
                    connection.danger_reason,
                ]
            )

    with full_summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "FromDevice",
                "ToDevice",
                "OperatingSystem",
                "IPAddress",
                "MACAddress",
                "ToIPAddress",
                "ToMACAddress",
                "Low Port",
                "Protocol",
                "Service",
                "Severity",
                "Vulnerability Score",
                "Boundary Group",
                "Reason",
            ]
        )
        for connection in connections:
            writer.writerow(
                [
                    connection.from_device,
                    connection.to_device,
                    connection.operating_system,
                    connection.ip_address,
                    connection.mac_address,
                    device_ip.get(connection.to_device, "Unknown"),
                    device_mac.get(connection.to_device, "Unknown"),
                    connection.low_port if connection.low_port is not None else "N/A",
                    connection.protocol,
                    connection.service,
                    connection.severity,
                    connection.vulnerability_score,
                    connection.boundary_group,
                    connection.danger_reason,
                ]
            )

    return high_risk_path, full_summary_path


def add_table_header(pdf: FPDF, headers: List[str], widths: List[float]) -> None:
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 8)
    for header, width in zip(headers, widths):
        pdf.cell(width, 8, header, border=1, align="C", fill=True)
    pdf.ln()


def ensure_page_space(pdf: FPDF, needed_height: float, headers: List[str], widths: List[float]) -> None:
    if pdf.get_y() + needed_height <= pdf.h - 12:
        return
    pdf.add_page()
    add_table_header(pdf, headers, widths)


def build_pdf_report(
    output_pdf: Path,
    diagram_path: Path,
    connections: List[Connection],
    device_os: Dict[str, str],
    device_ip: Dict[str, str],
    device_mac: Dict[str, str],
    parsed_at: datetime,
) -> Path:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False, margin=12)
    configure_pdf_fonts(pdf)

    total_connections = len(connections)
    total_high = sum(1 for conn in connections if conn.severity == "HIGH")
    total_medium = sum(1 for conn in connections if conn.severity == "MEDIUM")
    total_low = sum(1 for conn in connections if conn.severity == "LOW")

    # Page 1: Executive summary + visual diagram
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Network Security Audit Report", align="C")
    pdf.ln(10)

    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "", 11)
    summary_text = (
        f"Executive Summary (10-second view): Total High Risks: {total_high} | "
        f"Medium Risks: {total_medium} | Low Risks: {total_low} | Total Connections: {total_connections}"
    )
    pdf.multi_cell(0, 8, summary_text, border=1, fill=True)

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 7, f"Timestamp: {parsed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(7)

    if diagram_path.exists():
        max_w = pdf.w - 20
        max_h = max(pdf.h - pdf.get_y() - 12, 40)
        x = (pdf.w - max_w) / 2
        y = pdf.get_y() + 2
        pdf.image(str(diagram_path), x=x, y=y, w=max_w, h=max_h)

    # Page 2: Full connection table
    pdf.add_page()
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Connection Risk Table")
    pdf.ln(9)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Total Risk Count: {total_high + total_medium + total_low}")
    pdf.ln(6)
    pdf.cell(0, 6, f"Timestamp: {parsed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(6)
    pdf.ln(2)

    headers = [
        "From",
        "To",
        "From IP",
        "From MAC",
        "To IP",
        "To MAC",
        "Port",
        "Proto",
        "Service",
        "Severity",
        "Score",
    ]
    widths = [24, 24, 27, 32, 27, 32, 10, 12, 45, 16, 12]
    add_table_header(pdf, headers, widths)

    pdf.set_font("Arial", "", 6.5)
    for connection in connections:
        ensure_page_space(pdf, 7, headers, widths)

        if connection.severity == "HIGH":
            pdf.set_fill_color(255, 224, 224)
            fill = True
        else:
            pdf.set_fill_color(255, 255, 255)
            fill = False

        values = [
            connection.from_device,
            connection.to_device,
            connection.ip_address,
            connection.mac_address,
            device_ip.get(connection.to_device, "Unknown"),
            device_mac.get(connection.to_device, "Unknown"),
            str(connection.low_port) if connection.low_port is not None else "N/A",
            connection.protocol,
            connection.service,
            connection.severity,
            connection.vulnerability_score,
        ]

        for value, width in zip(values, widths):
            text = (value or "")[:40]
            pdf.cell(width, 7, text, border=1, fill=fill)
        pdf.ln()

    # Page 3: Device inventory
    pdf.add_page()
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Device Inventory")
    pdf.ln(10)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, "Devices listed from CSV content including IP, MAC, and operating system.")
    pdf.ln(6)
    pdf.ln(2)

    inv_headers = ["Device", "IP Address", "MAC Address", "Operating System"]
    inv_widths = [70, 55, 62, 90]
    add_table_header(pdf, inv_headers, inv_widths)
    pdf.set_font("Arial", "", 8)

    for device in sorted(device_os.keys()):
        ensure_page_space(pdf, 8, inv_headers, inv_widths)
        pdf.cell(inv_widths[0], 8, device[:30], border=1)
        pdf.cell(inv_widths[1], 8, device_ip.get(device, "Unknown")[:26], border=1)
        pdf.cell(inv_widths[2], 8, device_mac.get(device, "Unknown")[:30], border=1)
        pdf.cell(inv_widths[3], 8, device_os.get(device, "Unknown OS")[:34], border=1)
        pdf.ln()

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_pdf))
    return output_pdf


def configure_pdf_fonts(pdf: FPDF) -> None:
    """Use Arial when available on macOS; otherwise fallback to core fonts."""
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    bold_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
    ]

    regular = next((p for p in candidates if p.exists()), None)
    bold = next((p for p in bold_candidates if p.exists()), None)

    if regular:
        pdf.add_font("Arial", style="", fname=str(regular))
    if bold:
        pdf.add_font("Arial", style="B", fname=str(bold))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate network audit artifacts from PPSM CSV input."
    )
    parser.add_argument(
        "--diagram-outputs",
        choices=["mermaid-only", "visio-only", "both", "mydraw"],
        default="both",
        help=(
            "Select generated text-diagram formats. "
            "mermaid-only=write .mmd only, visio-only=write standard .vsdx only, "
            "both=write Mermaid + standard .vsdx, mydraw=write MyDraw ultra-safe .vsdx only."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    root = Path(__file__).resolve().parent
    csv_path = root / "datafiles" / "soteria-infra-PPSM.csv"
    output_dir = root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    connections, device_os, device_ip, device_mac, parsed_at = parse_csv(csv_path)

    diagram_prefix = output_dir / "soteria_network_diagram"
    diagram_path = build_diagram(diagram_prefix, connections, device_os, device_ip, device_mac)

    high_risk_csv, full_csv = write_summary_tables(output_dir, connections, device_ip, device_mac)

    mermaid_path = None
    visio_path = None
    visio_ultra_safe_path = None

    if args.diagram_outputs in {"mermaid-only", "both"}:
        mermaid_path = write_mermaid_diagram(output_dir, connections, device_os, device_ip, device_mac)

    if args.diagram_outputs in {"visio-only", "both"}:
        visio_path = write_visio_diagram(
            output_dir,
            connections,
            device_os,
            device_ip,
            device_mac,
            include_edges=True,
            output_filename="soteria_network_diagram.vsdx",
        )

    if args.diagram_outputs == "mydraw":
        visio_ultra_safe_path = write_visio_mydraw_ultra_safe(
            output_dir,
            connections,
            device_os,
            device_ip,
            device_mac,
        )

    pdf_path = output_dir / "soteria_network_security_report.pdf"
    build_pdf_report(pdf_path, diagram_path, connections, device_os, device_ip, device_mac, parsed_at)

    print("Completed network audit artifact generation:")
    print(f"- Diagram PNG: {diagram_path}")
    print(f"- High-risk summary CSV: {high_risk_csv}")
    print(f"- Full connection summary CSV: {full_csv}")
    if mermaid_path:
        print(f"- Mermaid diagram (.mmd): {mermaid_path}")
    if visio_path:
        print(f"- Microsoft Visio diagram (.vsdx): {visio_path}")
    if visio_ultra_safe_path:
        print(f"- Microsoft Visio diagram (.vsdx, MyDraw ultra-safe mode): {visio_ultra_safe_path}")
    print(f"- PDF report: {pdf_path}")


if __name__ == "__main__":
    main()
