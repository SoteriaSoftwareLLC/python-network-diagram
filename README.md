# Python Network Diagram generator

Using data collected from OpenRMF Professional (www.soteriasoft.com) we will use python to generate network diagrams as well as information for all of the devices, boundaries, and PPS for them to work on autogenerating a network diagram.


## MacOS Sonoma

You may need to run this to setup requests and call the Python3 scripts correctly.

```
python3 -m venv path/to/venv
source path/to/venv/bin/activate
python3 -m pip install graphviz
python3 -m pip install diagrams
```

# How to Run this

```bash
.venv/bin/python network_security_diagram_report.py
Completed network audit artifact generation:
- Diagram PNG: ./soteria/OpenRMFPro/python-network-diagram/outputs/soteria_network_diagram.png
- High-risk summary CSV: ./soteria/OpenRMFPro/python-network-diagram/outputs/high_risk_summary.csv
- Full connection summary CSV: ./soteria/OpenRMFPro/python-network-diagram/outputs/all_connections_summary.csv
- PDF report: ./soteria/OpenRMFPro/python-network-diagram/outputs/soteria_network_security_report.pdf
```


# GitHub Copilot Prompt once we had the XLSX and CSV file

```
given the datafiles/soteria-infra-PPSM.csv file perform the following
- read in a CSV file datafiles/soteria-infra-PPSM.csv
- the first row is the column names, data starts on the 2nd row
- use python with graphviz to draw a network diagram connecting machines with FromDevice to the ToDevice over the Low Port, Protocol and Service
- use the diagrams python library to create a high definition professional network diagram in a PNG format
- have a list of known High-Risk ports to flag as red when they appear
- if a Low Port is in that list of "High-Risk" ports labeled DANGER_PORTS (like 21/FTP, 23/Telnet, or 3389/RDP) the line will automatically turn Red and Bold to grab your attention
- have a yellow color on services that have a question mark in the name or are titled unknown
- add "Subnets" or "VLAN" groupings so that devices on the same network appear inside a labeled box
- along with the PNG, add a "Summary Table" output that the script generates alongside the image, listing all the flagged high-risk connections it found
- add a "Vulnerability Score" column to the table that ranks the risks as Low, Medium, or High based on the port number
  - incorporate a logic check that assigns a "Severity" (High, Medium, or Low) based on the port and the service being used
  - In the diagram, use line thickness to represent the score: a thick red line for High-risk vulnerabilities and a thin blue line for Low-risk ones
  - In the summary table, add a dedicated column for the score
- export this summary table into a PDF report along with the diagram image using the library fpdf
  - combine the Diagram Generation, the Security Audit logic, and a PDF Export function
  - Executive Summary: A gray-shaded box at the top of the first page gives a 10-second overview of the network's health (e.g., "Total High Risks: 3")
  - Page 1 (Visual): A high-resolution PNG of your network diagram centered on the page
  - Page 2 (Data): A formatted table containing every connection found in the CSV
    - Risk Highlighting: Rows marked as "HIGH" risk are automatically shaded Light Red in the PDF table to make them stand out to auditors
    - Clean Layout: It uses a standard Arial font and clear cell borders, making it suitable for professional submission
    - add a Total Risk Count and a Timestamp to calculate these statistics as it parses your CSV
  - Page 3: add a "Device Inventory" page at the end that lists every device by its MAC address and OS, regardless of whether it has a connection
```

Added this when all was said and done:

```
Can you add IPAddress and MACAddress as columns, after OperatingSystem and before "Low Port" and give unique IPs and MAC addresses to the device names? Use the IP Range 192.168.30.xxx as the pattern. Then incorporate the IP and MAC into the parsing, diagram, and reporting.
```

And the this:

```
Update PDF calls in network_security_diagram_report.py to remove fpdf2 deprecation warnings.  
Add destination endpoint identity columns (ToIPAddress, ToMACAddress) to connection summary exports if you want both endpoints explicit per row. 
Make the image wider so it works well in landscape mode
Make the PDF in landscape mode not portrait mode
```

Then iterated on questions around the PNG and making the PDF landscape for what I liked.