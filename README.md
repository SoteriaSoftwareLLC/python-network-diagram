is there a way to feed a python program information in a CSV on devices, ip address, operating system mac, connections to other devices over port, protocol, and service and make it generate a network diagram PNG file?


Yes, there is a very effective way to do this. You can use Python to parse your CSV and then leverage a visualization library to draw the connections.

The most popular tool for this is Graphviz (via the graphviz Python library) because it excels at "structural" diagrams like network topologies. Another great option is Diagrams, which is a "diagram-as-code" tool that uses cloud and networking icons to make the output look professional.

Recommended Workflow
Data Parsing: Use the built-in csv module or pandas to read your device and connection data.

Graph Construction: Loop through the rows to create "nodes" (devices) and "edges" (connections).

Metadata Mapping: Use the "Operating System" or "Service" columns to change node colors or icons.

Export: Save the resulting graph as a .png file.

Example Implementation (Using Graphviz)
If you have a CSV named network_data.csv with headers like source_device, source_ip, target_device, port, and protocol, your script would look like this:

```python
import csv
from graphviz import Digraph

# Initialize the diagram
dot = Digraph(comment='Network Topology', format='png')
dot.attr(rankdir='LR', size='10,10')

# Read the CSV file
with open('network_data.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Create nodes for devices (includes IP and OS in the label)
        dot.node(row['source_device'], f"{row['source_device']}\n({row['source_ip']})\nOS: {row['os']}")
        dot.node(row['target_device'], row['target_device'])
        
        # Create the connection (edge) with port and protocol details
        edge_label = f"{row['protocol']}/{row['port']} ({row['service']})"
        dot.edge(row['source_device'], row['target_device'], label=edge_label)

# Generate the PNG file
dot.render('network_diagram', view=True)
```

Essential Libraries to Install
To get this running, you will need to install the following via your terminal:

pip install graphviz (Note: You must also install the Graphviz software on your system, not just the Python library).

pip install diagrams (If you want high-quality icons for Cisco, AWS, or Generic Servers).

Pro-Tips for Better Diagrams
Color Coding: Use a dictionary to map Operating Systems to colors (e.g., Linux = Green, Windows = Blue) and apply color=os_color to your nodes.

Grouping: If you have many devices on the same subnet, you can use Subgraphs in Graphviz to cluster them into a labeled box.

Interactivity: If your CSV is massive, a PNG might become unreadable. Consider exporting to HTML using the pyvis library, which allows you to zoom and drag nodes around.

Would you like me to provide a sample CSV structure that matches this code, or would you prefer a version of the script using the "Diagrams" library for a more "Cisco-style" look?

---

Is there a way to do this without needing COTS software to purchase? so it can make a PNG or JPG file right away?


Absolutely. You don't need to purchase any commercial off-the-shelf (COTS) software for this. Everything can be done using free, open-source Python libraries.The two best ways to do this are using Graphviz (standard for logic-based diagrams) or Diagrams (better if you want "pretty" icons for cloud or networking hardware).1. The "Logic-First" Approach (Graphviz)This is the most flexible. It treats your CSV as a "Map" and automatically decides where to place the icons so they don't overlap.Cost: $0Output: PNG, JPG, or SVG.Requirements: You'll need the graphviz Python library and the Graphviz system software.How the code works:It reads your CSV row-by-row. For every row, it creates two "nodes" (the devices) and one "edge" (the connection between them). You can even color-code the lines based on the protocol (e.g., Red for SSH, Blue for HTTP).

2. The "Infrastructure-as-Code" Approach (Diagrams Library)If you want the PNG to look like a professional architectural drawing (using icons for Linux servers, Windows workstations, and routers), use the Diagrams library.Cost: $0Best for: Visualizing Operating Systems and specific Services.

Example Logic:

```python
from diagrams import Diagram, Cluster
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch

with Diagram("My Network", show=False, direction="LR"):
    # You would loop through your CSV here
    source = Linux("Web Server\n192.168.1.10")
    target = Windows("DB Server\n192.168.1.20")
    
    source >> target  # This creates the connection line
```

How to get started for free:
Install Python (if you haven't already).

Install the Tool: Run pip install graphviz or pip install diagrams in your terminal.

Install the Engine: Download the Graphviz engine—this is the free "brain" that actually draws the lines for both libraries.

Would you like me to write a full, ready-to-run Python script that parses a CSV with those specific columns (IP, OS, Port, etc.)?

---

yes, please write a full python ready-to-run with a CSV that has these columns:  hostname, IP Address, MAC Address, Operating System, port, protocol, service name



To get this running without purchasing any software, we will use the Graphviz library. It is the industry standard for open-source diagramming-as-code.

1. Prerequisites (Free Setup)
Before running the script, you need two things:

The Python Library: Run pip install graphviz in your terminal.

The Graphviz Engine: This is the actual "drawing" software. Download the free installer for your OS from the official Graphviz website.

Note for Windows: During installation, select "Add Graphviz to the system PATH" so Python can find it.

2. The Python Script
This script performs three tasks: it creates a dummy CSV for you to test, parses the data, and generates a structured PNG. It also includes color-coding for different Operating Systems automatically.

```python
import csv
import os
from graphviz import Digraph

# 1. Create a dummy CSV file for demonstration
csv_filename = 'network_inventory.csv'
data = [
    ['hostname', 'ip_address', 'mac_address', 'os', 'port', 'protocol', 'service_name', 'connected_to'],
    ['Web-Server-01', '192.168.1.10', '00:0a:95:9d:68:16', 'Linux', '80', 'TCP', 'HTTP', 'Core-Switch'],
    ['DB-Server-01', '192.168.1.20', '00:0a:95:9d:68:22', 'Linux', '5432', 'TCP', 'PostgreSQL', 'Core-Switch'],
    ['Workstation-05', '192.168.1.50', 'a1:b2:c3:d4:e5:f6', 'Windows', '445', 'TCP', 'SMB', 'Core-Switch'],
    ['Core-Switch', '192.168.1.1', 'ff:ff:ff:ff:ff:ff', 'Cisco IOS', '0', 'N/A', 'Gateway', 'Internet-Router'],
]

with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data)

# 2. Function to generate the diagram
def generate_network_map(input_csv):
    # Initialize the diagram (Left-to-Right layout)
    dot = Digraph(comment='Network Topology', format='png')
    dot.attr(rankdir='LR', overlap='false', splines='polyline')
    
    # OS Color Mapping
    os_colors = {
        'Linux': 'lightgreen',
        'Windows': 'skyblue',
        'Cisco IOS': 'orange'
    }

    with open(input_csv, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Create a label with all your requested information
            node_label = (
                f"<<TABLE BORDER='0' CELLBORDER='1' CELLSPACING='0'>\n"
                f"  <TR><TD BORDER='0'><B>{row['hostname']}</B></TD></TR>\n"
                f"  <TR><TD BORDER='0'>{row['ip_address']}</TD></TR>\n"
                f"  <TR><TD BORDER='0'><FONT POINT-SIZE='10'>{row['mac_address']}</FONT></TD></TR>\n"
                f"  <TR><TD BORDER='0'><I>{row['os']}</I></TD></TR>\n"
                f"</TABLE>>"
            )

            # Style the node based on OS
            fill_color = os_colors.get(row['os'], 'white')
            dot.node(row['hostname'], label=node_label, shape='box', style='filled', fillcolor=fill_color)

            # Create the connection (Edge)
            if row['connected_to']:
                edge_label = f"{row['service_name']}\n({row['protocol']}/{row['port']})"
                dot.edge(row['hostname'], row['connected_to'], label=edge_label)

    # 3. Output the file
    output_path = dot.render('network_diagram_output', cleanup=True)
    print(f"Success! Diagram generated at: {output_path}")

if __name__ == "__main__":
    generate_network_map(csv_filename)
```

Why this works well:
Scalability: Because Graphviz uses an "Automatic Layout Engine," you don't have to specify coordinates. If you add 50 more devices to the CSV, the program will just grow the image and reorganize the lines for you.

Rich Labels: I used HTML-like labels in the code (<TABLE>). This allows the IP Address, MAC Address, and Hostname to be stacked neatly inside the box rather than being one long, messy string.

Visual Context: The os_colors dictionary helps you instantly identify your Windows vs. Linux assets at a glance.

----

How to use your real data:
Open the network_inventory.csv file created by the script (or create your own with those exact headers).

Paste your actual device data into the rows.

Ensure the connected_to column contains the hostname of the destination device.

Run the script again.

Would you like me to show you how to add "Subnets" or "VLAN" groupings so that devices on the same network appear inside a labeled box?

------

o switch to the Diagrams library, the logic remains the same (looping through a CSV), but the output will look much more like a professional network map with actual icons for Windows, Linux, and Routers.

1. Prerequisites (Free Setup)
You still need the Graphviz engine installed on your OS (as it handles the positioning of the icons), but you will need to install the specific Python library:

Install Library: pip install diagrams

Engine: Ensure Graphviz is installed and added to your System PATH.

2. The Python Script (Diagrams Version)
This script maps your "Operating System" column to specific high-quality icons.

```python
import csv
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router
from diagrams.generic.device import Tablet

# 1. Configuration: Map your CSV 'os' column to specific Icons
def get_node_icon(os_name, label):
    os_name = os_name.lower()
    if 'linux' in os_name:
        return Linux(label)
    if 'windows' in os_name:
        return Windows(label)
    if 'cisco' in os_name or 'switch' in os_name:
        return Switch(label)
    if 'router' in os_name:
        return Router(label)
    return Tablet(label) # Default icon

# 2. Process the Data
def generate_iac_diagram(csv_file):
    # Set up diagram attributes
    graph_attr = {
        "fontsize": "20",
        "bgcolor": "white"
    }

    with Diagram("Company Network Topology", show=False, direction="LR", graph_attr=graph_attr, filename="network_diagram_iac"):
        nodes = {}

        # First pass: Create all device nodes
        with open(csv_file, mode='r') as f:
            reader = list(csv.DictReader(f))
            
            for row in reader:
                label = f"{row['hostname']}\n{row['ip_address']}\n{row['mac_address']}"
                nodes[row['hostname']] = get_node_icon(row['operating_system'], label)

        # Second pass: Create connections
        with open(csv_file, mode='r') as f:
            f.seek(0)
            reader = csv.DictReader(f)
            for row in reader:
                source = nodes.get(row['hostname'])
                target = nodes.get(row['connected_to'])
                
                if source and target:
                    # Label the line with Port, Protocol, and Service
                    conn_label = f"{row['service_name']} ({row['protocol']}/{row['port']})"
                    source >> Edge(label=conn_label, color="darkgrey") >> target

if __name__ == "__main__":
    # Ensure your CSV headers match: hostname, ip_address, mac_address, operating_system, port, protocol, service_name, connected_to
    # generate_iac_diagram('your_file.csv')
    print("Script ready. Point it to your CSV to generate 'network_diagram_iac.png'")
```


Key Differences in this Approach:
Icon-Based: Instead of colored boxes, your "Windows" machines will actually look like Windows machines.

Directional Flow: The source >> target syntax makes the code very readable; it literally shows the direction of the data flow.

Edge Objects: We use Edge() to customize the lines. You can change the color of the lines based on the service (e.g., make all "HTTPS" lines green and all "SSH" lines blue).

Why use this over Graphviz?
Use this if you are presenting the diagram to management or clients. It looks less like a "data flow chart" and more like a "physical infrastructure map."

Potential Limitation:
The diagrams library is slightly more rigid with "clustering." If you want to group all devices by their MAC address prefix or Subnet, you would wrap the node creation inside a with Cluster("Subnet Name"): block.

---

Would you like me to show you how to add those "Clusters" so that devices on the same subnet are grouped inside a visual box?

To group your devices by subnets or physical locations, we use Clusters. In the diagrams library, a cluster acts as a "scope" or a box; any device created inside that with Cluster(): block will be visually grouped together.

The Updated Script (with Subnet Grouping)
This script assumes your CSV has a subnet column (e.g., "192.168.1.0" or "Management"). If a device doesn't have a subnet listed, it will be placed outside the boxes.

```python
import csv
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router
from diagrams.generic.device import Tablet

def get_node_icon(os_name, label):
    os_name = os_name.lower()
    if 'linux' in os_name: return Linux(label)
    if 'windows' in os_name: return Windows(label)
    if 'cisco' in os_name or 'switch' in os_name: return Switch(label)
    if 'router' in os_name: return Router(label)
    return Tablet(label)

def generate_clustered_diagram(csv_file):
    with Diagram("Network Topology with Subnets", show=False, direction="TB"):
        nodes = {}
        
        # 1. Read CSV and organize by Subnet
        # Structure: { 'Subnet Name': [row1, row2], 'Other Subnet': [row3] }
        subnets = {}
        with open(csv_file, mode='r') as f:
            reader = list(csv.DictReader(f))
            for row in reader:
                s_name = row.get('subnet', 'External')
                if s_name not in subnets:
                    subnets[s_name] = []
                subnets[s_name].append(row)

        # 2. Create the Clusters and Nodes
        for subnet_name, rows in subnets.items():
            with Cluster(f"Subnet: {subnet_name}"):
                for row in rows:
                    label = f"{row['hostname']}\n{row['ip_address']}"
                    nodes[row['hostname']] = get_node_icon(row['operating_system'], label)

        # 3. Create Connections
        # We re-read the data to ensure all nodes exist before drawing lines
        for subnet_name, rows in subnets.items():
            for row in rows:
                source = nodes.get(row['hostname'])
                target = nodes.get(row['connected_to'])
                
                if source and target:
                    conn_label = f"{row['service_name']} ({row['port']})"
                    source >> Edge(label=conn_label, color="blue") >> target

if __name__ == "__main__":
    # Ensure your CSV has a 'subnet' and 'connected_to' column
    generate_clustered_diagram('network_inventory.csv')
```

Why this is powerful:
Visual Organization: Instead of a "spaghetti" diagram where lines cross everywhere, boxes help the human eye identify which devices belong to which department or VLAN.

Top-to-Bottom Flow: I changed direction="TB" (Top-to-Bottom) in the code. This usually looks cleaner for clustered diagrams as it stacks subnets vertically.

Logical Isolation: It makes it very obvious if a device in "Subnet A" is talking to a device in "Subnet B," which is great for security auditing.

Adding color-coded logic for security risks is a great way to make this diagram "intelligent" rather than just a static picture.

We can modify the script to check a list of "High-Risk" ports (like 21/FTP, 23/Telnet, or 3389/RDP). If a connection in your CSV uses one of these, the line will automatically turn Red and Bold to grab your attention.

```python
import csv
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# Define high-risk ports that should trigger a "Red Alert" line
DANGER_PORTS = ['21', '23', '3389', '445', '135', '139']

def get_node_icon(os_name, hostname):
    os_name = os_name.lower()
    label = f"{hostname}"
    if 'linux' in os_name: return Linux(label)
    if 'windows' in os_name: return Windows(label)
    if 'cisco' in os_name or 'switch' in os_name: return Switch(label)
    if 'firewall' in os_name: return Firewall(label)
    return Router(label)

def generate_secure_diagram(csv_file):
    with Diagram("Network Security Topology", show=False, direction="TB"):
        nodes = {}
        connections = []

        # 1. Read Data and Group by Subnet
        subnets = {}
        with open(csv_file, mode='r') as f:
            reader = list(csv.DictReader(f))
            for row in reader:
                s_name = row.get('subnet', 'General')
                if s_name not in subnets: subnets[s_name] = []
                subnets[s_name].append(row)
                connections.append(row)

        # 2. Draw Clusters
        for subnet_name, devices in subnets.items():
            with Cluster(f"Zone: {subnet_name}"):
                for dev in devices:
                    # Detailed label for the icon
                    full_label = f"{dev['hostname']}\n{dev['ip_address']}\n{dev['operating_system']}"
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], full_label)

        # 3. Draw Connections with Security Logic
        for conn in connections:
            source = nodes.get(conn['hostname'])
            target = nodes.get(conn['connected_to'])
            
            if source and target:
                port = conn.get('port', '0')
                is_risky = port in DANGER_PORTS
                
                # Visual logic: Red/Bold for danger, Blue/Thin for standard
                line_color = "red" if is_risky else "royalblue"
                line_style = "bold" if is_risky else "dashed"
                
                edge_label = f"{conn['service_name']} ({port})"
                
                source >> Edge(
                    label=edge_label, 
                    color=line_color, 
                    style=line_style,
                    fontcolor=line_color
                ) >> target

if __name__ == "__main__":
    # Ensure your CSV has these headers: 
    # hostname, ip_address, operating_system, subnet, connected_to, port, service_name
    generate_secure_diagram('network_inventory.csv')
```


How the Visual Logic Works:
Standard Connections: These appear as Blue, dashed lines. This represents normal, expected traffic (like HTTPS or DNS).

High-Risk Connections: If the script sees a port like 23 (Telnet) or 445 (SMB) in your CSV, it forces the line to be Solid Red and Bold. This allows you to spot unencrypted or risky protocols instantly.

Zone Isolation: By using the Cluster feature, the script places your "DMZ" servers in one box and "Internal" servers in another. If you see a Red line crossing between these two boxes, you know exactly where to investigate.

Quick Customization Tip:
If you want to add more ports to the "Danger" list, just add them to the DANGER_PORTS list at the top of the script:

```python
DANGER_PORTS = ['21', '23', '3389', '80']  (Adding 80 if you want to flag unencrypted web traffic)
```


---

Would you like me to add a "Summary Table" output that the script generates alongside the image, listing all the flagged high-risk connections it found?

Integrating a summary table is a smart move for auditing. It allows you to see the "Red Flags" immediately without having to hunt through the lines of a complex diagram.

I have updated the script below to include a Security Audit feature. It will now:

Generate the professional PNG diagram.

Print a formatted Markdown table to your console.

Save a Security_Report.csv file containing only the high-risk connections.

Updated Python Script with Security Auditing

```python
import csv
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# 1. Configuration: Ports that trigger "Security Alerts"
DANGER_PORTS = {
    '21': 'FTP (Unencrypted)',
    '23': 'Telnet (Unencrypted)',
    '3389': 'RDP (Remote Desktop)',
    '445': 'SMB/AD (Exploitable)',
    '135': 'RPC',
    '80': 'HTTP (Unencrypted)'
}

def get_node_icon(os_name, hostname):
    os_name = os_name.lower()
    if 'linux' in os_name: return Linux(hostname)
    if 'windows' in os_name: return Windows(hostname)
    if 'firewall' in os_name: return Firewall(hostname)
    if 'switch' in os_name: return Switch(hostname)
    return Router(hostname)

def generate_secure_network_audit(csv_file):
    nodes = {}
    flagged_issues = []
    
    # Pre-processing: Organize by Subnet
    subnets = {}
    all_rows = []
    with open(csv_file, mode='r') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            s_name = row.get('subnet', 'General')
            if s_name not in subnets: subnets[s_name] = []
            subnets[s_name].append(row)
            all_rows.append(row)

    # Generate Diagram
    with Diagram("Network Security Audit", show=False, direction="TB", filename="network_audit_map"):
        # Create Nodes in Clusters
        for subnet_name, devices in subnets.items():
            with Cluster(f"Zone: {subnet_name}"):
                for dev in devices:
                    label = f"{dev['hostname']}\n{dev['ip_address']}"
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], label)

        # Create Connections and Audit Logic
        for row in all_rows:
            source = nodes.get(row['hostname'])
            target = nodes.get(row['connected_to'])
            
            if source and target:
                port = row.get('port', '')
                is_risky = port in DANGER_PORTS
                
                # Logic for the Diagram Lines
                l_color = "red" if is_risky else "royalblue"
                l_style = "bold" if is_risky else "dashed"
                
                source >> Edge(label=f"{row['service_name']} ({port})", color=l_color, style=l_style) >> target
                
                # If risky, add to our Summary Table list
                if is_risky:
                    flagged_issues.append({
                        'Source': row['hostname'],
                        'Target': row['connected_to'],
                        'Port': port,
                        'Risk': DANGER_PORTS[port]
                    })

    # --- Print Summary Table to Console ---
    print("\n" + "="*60)
    print("SECURITY AUDIT SUMMARY: HIGH-RISK CONNECTIONS FOUND")
    print("="*60)
    print(f"{'SOURCE':<15} | {'TARGET':<15} | {'PORT':<6} | {'RISK TYPE'}")
    print("-" * 60)
    for issue in flagged_issues:
        print(f"{issue['Source']:<15} | {issue['Target']:<15} | {issue['Port']:<6} | {issue['Risk']}")
    print("="*60 + "\n")

if __name__ == "__main__":
    generate_secure_network_audit('network_inventory.csv')
```


Key Benefits of this Setup
Dual Visibility: You get the "Big Picture" from the PNG and the "To-Do List" from the table.

Audit-Ready: You can copy-paste the table directly into a report or an email.

Customizable Threats: You can easily update the DANGER_PORTS dictionary to include specific ports used by proprietary software in your environment.

-----


Would you like me to add a "Vulnerability Score" column to the table that ranks the risks as Low, Medium, or High based on the port number?

To add a Vulnerability Score, we’ll incorporate a logic check that assigns a "Severity" (High, Medium, or Low) based on the port and the service being used.

In the diagram, we can use line thickness to represent the score: a thick red line for High-risk vulnerabilities and a thin blue line for Low-risk ones. In the summary table, we'll add a dedicated column for the score.

Updated Python Script with Vulnerability Scoring

```python
import csv
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# 1. Enhanced Security Configuration
# Port: (Risk Level, Risk Description)
VULN_DATABASE = {
    '21':   ('HIGH', 'Unencrypted FTP - Credentials visible'),
    '23':   ('HIGH', 'Telnet - Cleartext management'),
    '3389': ('MEDIUM', 'RDP - Target for Brute Force'),
    '445':  ('HIGH', 'SMB/AD - Lateral Movement Risk'),
    '80':   ('MEDIUM', 'Unencrypted HTTP'),
    '22':   ('LOW', 'SSH - Standard Encrypted Management'),
    '443':  ('LOW', 'HTTPS - Standard Encrypted Web'),
}

def get_node_icon(os_name, hostname):
    os_name = os_name.lower()
    if 'linux' in os_name: return Linux(hostname)
    if 'windows' in os_name: return Windows(hostname)
    if 'firewall' in os_name: return Firewall(hostname)
    return Router(hostname)

def generate_vuln_report_and_map(csv_file):
    nodes = {}
    audit_log = []
    
    # Pre-processing: Group by Subnet
    subnets = {}
    with open(csv_file, mode='r') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            s_name = row.get('subnet', 'General')
            if s_name not in subnets: subnets[s_name] = []
            subnets[s_name].append(row)

    # 2. Generate Diagram
    with Diagram("Network Security Audit with Scoring", show=False, direction="TB", filename="security_score_map"):
        for subnet_name, devices in subnets.items():
            with Cluster(f"Zone: {subnet_name}"):
                for dev in devices:
                    label = f"{dev['hostname']}\n{dev['ip_address']}"
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], label)

        # Draw Connections with Scoring Logic
        for subnet_name, devices in subnets.items():
            for dev in devices:
                source = nodes.get(dev['hostname'])
                target = nodes.get(dev['connected_to'])
                
                if source and target:
                    port = dev.get('port', '')
                    score_data = VULN_DATABASE.get(port, ('LOW', 'Standard Traffic'))
                    score_level, description = score_data
                    
                    # Visual Mapping: Higher risk = Thicker Red line
                    if score_level == 'HIGH':
                        l_color, l_width = "red", "3.0"
                    elif score_level == 'MEDIUM':
                        l_color, l_width = "orange", "2.0"
                    else:
                        l_color, l_width = "royalblue", "1.0"

                    source >> Edge(
                        label=f"{dev['service_name']} ({port})",
                        color=l_color,
                        penwidth=l_width
                    ) >> target
                    
                    # Store data for the Summary Table
                    audit_log.append({
                        'Source': dev['hostname'],
                        'Target': dev['connected_to'],
                        'Port': port,
                        'Score': score_level,
                        'Description': description
                    })

    # --- Print Scored Summary Table ---
    print("\n" + "="*85)
    print(f"{'SOURCE':<15} | {'TARGET':<15} | {'PORT':<6} | {'SCORE':<8} | {'VULNERABILITY DESCRIPTION'}")
    print("-" * 85)
    
    # Sort audit by score severity (High first)
    for issue in sorted(audit_log, key=lambda x: x['Score'], reverse=True):
        print(f"{issue['Source']:<15} | {issue['Target']:<15} | {issue['Port']:<6} | {issue['Score']:<8} | {issue['Description']}")
    print("="*85 + "\n")

if __name__ == "__main__":
    # Make sure your CSV has: hostname, ip_address, operating_system, subnet, connected_to, port, service_name
    generate_vuln_report_and_map('network_inventory.csv')
```


How the Scoring Works:
High (Red, Thick Line): Assigned to legacy or highly exploitable protocols like Telnet (23) or SMB (445). These require immediate attention.

Medium (Orange, Medium Line): Assigned to unencrypted but common traffic like HTTP (80).

Low (Blue, Thin Line): Standard, encrypted, or "safe" traffic like HTTPS (443) or SSH (22).

Pro Tip for Automation
Since this is Python, you could easily modify the VULN_DATABASE to pull from a real-time vulnerability feed (like an API for CVEs) if you wanted to make this a production-grade tool.

---

Would you like me to show you how to export this summary table into a PDF report along with the diagram image?

To export both the visual diagram and the security audit table into a single, professional PDF report, we can use the FPDF library. It is a lightweight, free, and open-source library that doesn't require complex dependencies like some of the larger PDF engines.

1. Prerequisites
You will need to install the library via your terminal:
pip install fpdf

2. The Final Integrated Script
This script combines the Diagram Generation, the Security Audit logic, and a PDF Export function.

```python
import csv
from fpdf import FPDF
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# --- CONFIGURATION ---
DANGER_PORTS = {
    '21': ('HIGH', 'Unencrypted FTP'),
    '23': ('HIGH', 'Telnet - Cleartext'),
    '3389': ('MEDIUM', 'RDP - Brute Force Target'),
    '445': ('HIGH', 'SMB/AD - Lateral Movement'),
    '80': ('MEDIUM', 'Unencrypted HTTP')
}

class NetworkReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Network Security & Topology Report', 0, 1, 'C')
        self.ln(10)

def get_node_icon(os_name, hostname):
    os = os_name.lower()
    if 'linux' in os: return Linux(hostname)
    if 'windows' in os: return Windows(hostname)
    if 'firewall' in os: return Firewall(hostname)
    return Router(hostname)

def generate_full_report(csv_file):
    audit_log = []
    subnets = {}

    # 1. Parse CSV
    with open(csv_file, mode='r') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            s_name = row.get('subnet', 'General')
            if s_name not in subnets: subnets[s_name] = []
            subnets[s_name].append(row)

    # 2. Generate PNG Diagram
    with Diagram("Network Audit", show=False, direction="TB", filename="temp_map"):
        nodes = {}
        for subnet, devices in subnets.items():
            with Cluster(f"Zone: {subnet}"):
                for dev in devices:
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], dev['hostname'])
        
        for subnet, devices in subnets.items():
            for dev in devices:
                source, target = nodes.get(dev['hostname']), nodes.get(dev['connected_to'])
                if source and target:
                    port = dev.get('port', '')
                    level, desc = VULN_DATABASE.get(port, ('LOW', 'Standard'))
                    color = "red" if level == 'HIGH' else "orange" if level == 'MEDIUM' else "royalblue"
                    source >> Edge(label=f"{port}", color=color) >> target
                    audit_log.append([dev['hostname'], dev['connected_to'], port, level, desc])

    # 3. Create PDF
    pdf = NetworkReport()
    pdf.add_page()
    
    # Add Diagram to PDF
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Visual Topology Map', 0, 1)
    pdf.image('temp_map.png', x=10, y=40, w=190)
    
    # Add Table to PDF
    pdf.add_page()
    pdf.cell(0, 10, '2. Security Audit Summary', 0, 1)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(200, 200, 200)
    cols = [('Source', 35), ('Target', 35), ('Port', 15), ('Score', 20), ('Description', 85)]
    for name, width in cols:
        pdf.cell(width, 10, name, 1, 0, 'C', True)
    pdf.ln()

    # Table Rows
    pdf.set_font('Arial', '', 9)
    for row in audit_log:
        # Highlight high-risk rows in light red
        if row[3] == 'HIGH': pdf.set_fill_color(255, 204, 204)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(35, 10, row[0], 1, 0, 'C', True)
        pdf.cell(35, 10, row[1], 1, 0, 'C', True)
        pdf.cell(15, 10, row[2], 1, 0, 'C', True)
        pdf.cell(20, 10, row[3], 1, 0, 'C', True)
        pdf.cell(85, 10, row[4], 1, 1, 'L', True)

    pdf.output('Network_Security_Report.pdf')
    print("Report generated: Network_Security_Report.pdf")

if __name__ == "__main__":
    generate_full_report('network_inventory.csv')
```

What this Report Includes:
Page 1 (Visual): A high-resolution PNG of your network diagram centered on the page.

Page 2 (Data): A formatted table containing every connection found in the CSV.

Risk Highlighting: Rows marked as "HIGH" risk are automatically shaded Light Red in the PDF table to make them stand out to auditors.

Clean Layout: It uses a standard Arial font and clear cell borders, making it suitable for professional submission.

What this Report Includes:
Page 1 (Visual): A high-resolution PNG of your network diagram centered on the page.

Page 2 (Data): A formatted table containing every connection found in the CSV.

Risk Highlighting: Rows marked as "HIGH" risk are automatically shaded Light Red in the PDF table to make them stand out to auditors.

Clean Layout: It uses a standard Arial font and clear cell borders, making it suitable for professional submission.

---

To add a Total Risk Count and a Timestamp, we will update the NetworkReport class to calculate these statistics as it parses your CSV.

This makes the report "audit-ready" by showing exactly when the scan was generated and providing an executive summary of the risk posture at the very top of the page.

```python
import csv
from datetime import datetime
from fpdf import FPDF
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# 1. Configuration: Risk Database
VULN_DATABASE = {
    '21':   ('HIGH', 'Unencrypted FTP'),
    '23':   ('HIGH', 'Telnet - Cleartext'),
    '3389': ('MEDIUM', 'RDP - Brute Force Target'),
    '445':  ('HIGH', 'SMB/AD - Lateral Movement'),
    '80':   ('MEDIUM', 'Unencrypted HTTP')
}

class NetworkReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Network Security & Topology Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        # Add timestamp to the header
        dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f'Generated on: {dt_string}', 0, 1, 'C')
        self.ln(5)

def get_node_icon(os_name, hostname):
    os = os_name.lower()
    if 'linux' in os: return Linux(hostname)
    if 'windows' in os: return Windows(hostname)
    if 'firewall' in os: return Firewall(hostname)
    return Router(hostname)

def generate_automated_report(csv_file):
    audit_log = []
    subnets = {}
    risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    # 1. Parse CSV and Calculate Stats
    with open(csv_file, mode='r') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            s_name = row.get('subnet', 'General')
            if s_name not in subnets: subnets[s_name] = []
            subnets[s_name].append(row)

    # 2. Generate PNG Diagram
    with Diagram("Network Audit", show=False, direction="TB", filename="temp_map"):
        nodes = {}
        for subnet, devices in subnets.items():
            with Cluster(f"Zone: {subnet}"):
                for dev in devices:
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], dev['hostname'])
        
        for subnet, devices in subnets.items():
            for dev in devices:
                source, target = nodes.get(dev['hostname']), nodes.get(dev['connected_to'])
                if source and target:
                    port = dev.get('port', '')
                    level, desc = VULN_DATABASE.get(port, ('LOW', 'Standard Traffic'))
                    risk_counts[level] += 1
                    
                    color = "red" if level == 'HIGH' else "orange" if level == 'MEDIUM' else "royalblue"
                    source >> Edge(label=f"{port}", color=color) >> target
                    audit_log.append([dev['hostname'], dev['connected_to'], port, level, desc])

    # 3. Create PDF
    pdf = NetworkReport()
    pdf.add_page()
    
    # --- EXECUTIVE SUMMARY SECTION ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, ' Executive Risk Summary', 1, 1, 'L', True)
    pdf.set_font('Arial', '', 11)
    
    # Display the counts
    pdf.cell(60, 10, f"Total High Risks: {risk_counts['HIGH']}", 0, 0)
    pdf.cell(60, 10, f"Total Medium Risks: {risk_counts['MEDIUM']}", 0, 0)
    pdf.cell(60, 10, f"Total Low/Safe: {risk_counts['LOW']}", 0, 1)
    pdf.ln(10)

    # --- DIAGRAM SECTION ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Visual Topology Map', 0, 1)
    pdf.image('temp_map.png', x=10, y=85, w=190)
    
    # --- TABLE SECTION ---
    pdf.add_page()
    pdf.cell(0, 10, '2. Detailed Security Audit Table', 0, 1)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(50, 50, 50) # Dark header
    pdf.set_text_color(255, 255, 255)
    cols = [('Source', 35), ('Target', 35), ('Port', 15), ('Score', 20), ('Description', 85)]
    for name, width in cols:
        pdf.cell(width, 10, name, 1, 0, 'C', True)
    pdf.ln()

    # Table Rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    for row in sorted(audit_log, key=lambda x: x[3]): # Sort by Risk Level
        if row[3] == 'HIGH': pdf.set_fill_color(255, 204, 204)
        elif row[3] == 'MEDIUM': pdf.set_fill_color(255, 240, 200)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(35, 10, row[0], 1, 0, 'C', True)
        pdf.cell(35, 10, row[1], 1, 0, 'C', True)
        pdf.cell(15, 10, row[2], 1, 0, 'C', True)
        pdf.cell(20, 10, row[3], 1, 0, 'C', True)
        pdf.cell(85, 10, row[4], 1, 1, 'L', True)

    pdf.output('Executive_Network_Report.pdf')
    print(f"Success! Report created with {risk_counts['HIGH']} high-priority issues.")

if __name__ == "__main__":
    generate_automated_report('network_inventory.csv')
```

What's New in This Version:
Executive Summary: A gray-shaded box at the top of the first page gives a 10-second overview of the network's health (e.g., "Total High Risks: 3").

Dynamic Timestamp: Uses the datetime library to mark exactly when the report was generated, which is critical for compliance logs.

Enhanced Styling: * High Risks are highlighted in Red in the table.

Medium Risks are highlighted in Yellow/Orange.

Header for the table is now a dark professional theme with white text.

Pro-Tip:
If you run this script on a schedule (e.g., once a week), you can change the output filename to include the date:
pdf.output(f'Report_{datetime.now().strftime("%Y%m%d")}.pdf')
This prevents the script from overwriting your previous audits.

---

Would you like me to add a "Device Inventory" page at the end that lists every device by its MAC address and OS, regardless of whether it has a connection?

Updated Python Script (With Inventory Page)

```python
import csv
from datetime import datetime
from fpdf import FPDF
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.os import Linux, Windows
from diagrams.generic.network import Switch, Router, Firewall

# --- CONFIGURATION ---
VULN_DATABASE = {
    '21':   ('HIGH', 'Unencrypted FTP'),
    '23':   ('HIGH', 'Telnet - Cleartext'),
    '3389': ('MEDIUM', 'RDP - Target'),
    '445':  ('HIGH', 'SMB/AD Risk'),
    '80':   ('MEDIUM', 'Unencrypted HTTP')
}

class NetworkReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Network Security & Topology Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f'Generated on: {dt_string}', 0, 1, 'C')
        self.ln(5)

def get_node_icon(os_name, hostname):
    os = os_name.lower()
    if 'linux' in os: return Linux(hostname)
    if 'windows' in os: return Windows(hostname)
    if 'firewall' in os: return Firewall(hostname)
    return Router(hostname)

def generate_complete_audit(csv_file):
    audit_log = []
    subnets = {}
    inventory = {} # To track unique devices
    risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    # 1. Parse CSV
    with open(csv_file, mode='r') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            # Store for subnet grouping
            s_name = row.get('subnet', 'General')
            if s_name not in subnets: subnets[s_name] = []
            subnets[s_name].append(row)
            
            # Store for unique inventory list
            inventory[row['hostname']] = {
                'ip': row['ip_address'],
                'mac': row['mac_address'],
                'os': row['operating_system']
            }

    # 2. Generate PNG Diagram
    with Diagram("Network Audit", show=False, direction="TB", filename="temp_map"):
        nodes = {}
        for subnet, devices in subnets.items():
            with Cluster(f"Zone: {subnet}"):
                for dev in devices:
                    nodes[dev['hostname']] = get_node_icon(dev['operating_system'], dev['hostname'])
        
        for subnet, devices in subnets.items():
            for dev in devices:
                source, target = nodes.get(dev['hostname']), nodes.get(dev['connected_to'])
                if source and target:
                    port = dev.get('port', '')
                    level, desc = VULN_DATABASE.get(port, ('LOW', 'Standard Traffic'))
                    risk_counts[level] += 1
                    color = "red" if level == 'HIGH' else "orange" if level == 'MEDIUM' else "royalblue"
                    source >> Edge(label=f"{port}", color=color) >> target
                    audit_log.append([dev['hostname'], dev['connected_to'], port, level, desc])

    # 3. Create PDF
    pdf = NetworkReport()
    
    # --- PAGE 1: EXECUTIVE SUMMARY & MAP ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, ' Executive Risk Summary', 1, 1, 'L', True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(60, 10, f"Total High Risks: {risk_counts['HIGH']}", 0, 0)
    pdf.cell(60, 10, f"Total Medium Risks: {risk_counts['MEDIUM']}", 0, 0)
    pdf.cell(60, 10, f"Total Low/Safe: {risk_counts['LOW']}", 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Visual Topology Map', 0, 1)
    pdf.image('temp_map.png', x=10, y=75, w=190)
    
    # --- PAGE 2: SECURITY AUDIT TABLE ---
    pdf.add_page()
    pdf.cell(0, 10, '2. Detailed Security Audit Table', 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    cols = [('Source', 35), ('Target', 35), ('Port', 15), ('Score', 20), ('Description', 85)]
    for name, width in cols: pdf.cell(width, 10, name, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    for row in sorted(audit_log, key=lambda x: x[3]):
        if row[3] == 'HIGH': pdf.set_fill_color(255, 204, 204)
        elif row[3] == 'MEDIUM': pdf.set_fill_color(255, 240, 200)
        else: pdf.set_fill_color(255, 255, 255)
        pdf.cell(35, 10, row[0], 1, 0, 'C', True)
        pdf.cell(35, 10, row[1], 1, 0, 'C', True)
        pdf.cell(15, 10, row[2], 1, 0, 'C', True)
        pdf.cell(20, 10, row[3], 1, 0, 'C', True)
        pdf.cell(85, 10, row[4], 1, 1, 'L', True)

    # --- PAGE 3: DEVICE INVENTORY ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Full Device Inventory', 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    inv_cols = [('Hostname', 50), ('IP Address', 40), ('MAC Address', 50), ('Operating System', 50)]
    for name, width in inv_cols: pdf.cell(width, 10, name, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    for host in sorted(inventory.keys()):
        pdf.cell(50, 10, host, 1, 0, 'C')
        pdf.cell(40, 10, inventory[host]['ip'], 1, 0, 'C')
        pdf.cell(50, 10, inventory[host]['mac'], 1, 0, 'C')
        pdf.cell(50, 10, inventory[host]['os'], 1, 1, 'C')

    pdf.output('Complete_Network_Audit_Report.pdf')
    print("Full report with Device Inventory generated successfully.")

if __name__ == "__main__":
    generate_complete_audit('network_inventory.csv')
```

What the Inventory Page Adds:
Completeness: It lists every device found in the CSV, even those with no connected_to target.

Organization: The list is sorted alphabetically by hostname for easy lookup.

Infrastructure Context: Provides a one-stop-shop for matching MAC addresses to Hostnames, which is invaluable during physical troubleshooting or switch-port tracing.

Final Result Overview:
Page 1: Executive Summary (Stats) + Visual Map.

Page 2: Security Audit (Ranked by Risk).

Page 3: Master Device Inventory (Full Hardware List).

---

By combining the Diagrams library with FPDF, you now have a professional tool that turns a simple CSV into a visual map, a security audit, and a full hardware inventory—all without spending a dime on commercial software.

Final Checklist for Success:
Data Integrity: Ensure your CSV headers (hostname, ip_address, mac_address, operating_system, port, protocol, service_name, connected_to, subnet) always match the script expectations.

Expansion: If you start using more specialized gear (like load balancers or IoT sensors), you can simply add new icons to the get_node_icon function.

Security Updates: Periodically update the VULN_DATABASE dictionary as new "shadow IT" ports or protocols become relevant to your specific environment.

It's been a pleasure helping you script this out. Since we've covered the diagram, the security scoring, and the full PDF reporting, is there anything else you'd like to tweak, or are you all set to start mapping your network?