#!/usr/bin/env python3
"""
OCVS EMEA Availability Dashboard Generator
Creates a static HTML page showing today's availability from capacity_report.json
"""

import json
import datetime
from pathlib import Path

def get_status_color(status):
    """Return CSS color class based on availability status"""
    status_map = {
        "AVAILABLE": "status-available",
        "OUT_OF_HOST_CAPACITY": "status-unavailable", 
        "HARDWARE_NOT_SUPPORTED": "status-unsupported"
    }
    return status_map.get(status, "status-unknown")

def calculate_availability_data(data, ads):
    """Calculate the percentage of days each cell was AVAILABLE and collect status data for tooltips"""
    availability_count = {ad: {} for ad in ads}
    status_data = {ad: {} for ad in ads}
    total_days = len(data)
    
    for date, ad_data in data.items():
        for ad, shape_data in ad_data.items():
            if ad not in availability_count:
                availability_count[ad] = {}
                status_data[ad] = {}
            for shape, fd_data in shape_data.items():
                if shape not in availability_count[ad]:
                    availability_count[ad][shape] = {fd: 0 for fd in fd_data["fault_domains"].keys()}
                    status_data[ad][shape] = {fd: [] for fd in fd_data["fault_domains"].keys()}
                for fd, status_info in fd_data["fault_domains"].items():
                    if fd not in availability_count[ad][shape]:
                        availability_count[ad][shape][fd] = 0
                        status_data[ad][shape][fd] = []
                    if status_info["availability_status"] == "AVAILABLE":
                        availability_count[ad][shape][fd] += 1
                    status_data[ad][shape][fd].append((date, status_info["availability_status"]))
    
    availability_percentage = {ad: {shape: {fd: (count / total_days) * 100 for fd, count in fd_counts.items()} for shape, fd_counts in shape_counts.items()} for ad, shape_counts in availability_count.items()}
    return availability_percentage, status_data

def generate_html(data, target_date, availability_percentage, status_data):
    """Generate the HTML content for the availability dashboard"""
    
    # Get all ADs and shapes from the data
    ads = list(data.keys())
    shapes = set()
    
    for ad_data in data.values():
        for shape in ad_data.keys():
            shapes.add(shape)
    
    shapes = sorted(list(shapes))
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCI BM Availability (EMEA)</title>
    <style>
        * {{{{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}}}
        
        body {{{{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}}}
        
        .container {{{{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}}}
        
        .header {{{{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}}}
        
        .header h1 {{{{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}}}
        
        .header .date {{{{
            font-size: 1.2em;
            opacity: 0.9;
        }}}}
        
        .table-container {{{{
            padding: 30px;
            overflow-x: auto;
        }}}}
        
        table {{{{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}}}
        
        th {{{{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 15px 10px;
            text-align: center;
            font-weight: 600;
            font-size: 0.9em;
            border: 1px solid #2980b9;
        }}}}
        
        th:first-child {{{{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            text-align: left;
            padding-left: 20px;
        }}}}
        
        td {{{{
            padding: 8px 10px;
            text-align: center;
            border: 1px solid #ecf0f1;
            font-size: 0.85em;
            font-weight: 500;
        }}}}
        
        .ad-row {{{{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
            text-align: left;
            padding-left: 20px;
        }}}}
        
        .status-available {{{{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            border-radius: 5px;
            font-weight: 600;
        }}}}
        
        .status-unavailable {{{{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            border-radius: 5px;
            font-weight: 600;
        }}}}
        
        .status-unsupported {{{{
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
            color: white;
            border-radius: 5px;
            font-weight: 600;
        }}}}
        
        .status-unknown {{{{
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
            color: white;
            border-radius: 5px;
            font-weight: 600;
        }}}}
        
        .legend {{{{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}}}
        
        .legend-item {{{{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            font-weight: 500;
        }}}}
        
        .legend-color {{{{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}}}
        
        .footer {{{{
            background: #ecf0f1;
            padding: 20px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}}}
        
        @media (max-width: 768px) {{{{
            .container {{{{
                margin: 10px;
                border-radius: 10px;
            }}}}
            
            .header h1 {{{{
                font-size: 2em;
            }}}}
            
            .table-container {{{{
                padding: 15px;
            }}}}
            
            th, td {{{{
                padding: 8px 5px;
                font-size: 0.75em;
            }}}}
        }}}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OCI BM Availability (EMEA)</h1>
            <div class="date">Latest Report Date: {target_date}</div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>AD / Shape</th>
"""
    
    # Add Shape headers with colspan for fault domains
    for shape in shapes:
        html += f'                        <th colspan="3">{shape}</th>\n'
    
    html += """                    </tr>
                    <tr>
                        <th></th>
"""
    
    # Add Fault Domain headers
    for shape in shapes:
        for fd in ["FD1", "FD2", "FD3"]:
            html += f'                        <th>{fd}</th>\n'
    
    html += """                    </tr>
                </thead>
                <tbody>
"""
    
    # Generate rows for each AD
    for ad in ads:
        # AD row
        html += f'                    <tr>\n                        <td class="ad-row">{ad}</td>\n'
        
        for shape in shapes:
            for fd in ["FAULT-DOMAIN-1", "FAULT-DOMAIN-2", "FAULT-DOMAIN-3"]:
                if shape in data[ad] and fd in data[ad][shape]["fault_domains"]:
                    status = data[ad][shape]["fault_domains"][fd]["availability_status"]
                    color_class = get_status_color(status)
                    percentage = availability_percentage[ad][shape][fd]
                    tooltip_data = status_data[ad][shape][fd]
                    # Sort tooltip data by date in descending order
                    tooltip_data_sorted = sorted(tooltip_data, key=lambda x: x[0], reverse=True)
                    tooltip_text = ', '.join([f'{date}: {status}' for date, status in tooltip_data_sorted])
                    html += f'                        <td class="{color_class}" title="{tooltip_text}">{percentage:.0f}%</td>\n'
                else:
                    html += '                        <td class="status-unknown" title="No data">0.0%</td>\n'
        
        html += '                    </tr>\n'
    
    html += """                </tbody>
            </table>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color status-available"></div>
                    <span>Available</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color status-unavailable"></div>
                    <span>Out of Host Capacity</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color status-unsupported"></div>
                    <span>Hardware Not Supported</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color status-unknown"></div>
                    <span>Unknown/Not Available</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Note: This information is gathered using the <a href="https://docs.oracle.com/en-us/iaas/tools/python/latest/api/core/client/oci.core.ComputeClient.html#oci.core.ComputeClient.create_compute_capacity_report">OCI Compute Capacity Report API</a>.</p>
            <p>The report indicates whether an instance is available for a specific shape in a given AD and Fault Domain, but does not show the number of instances available.</p>
            <p>The percentage shows the Availability over the last 30 days.</p>
            <p>Generated on {generation_time} | OCVS EMEA Availability Dashboard</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Format the generation time
    generation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = html.format(generation_time=generation_time)
    
    return html

def main():
    """Main function to generate the availability dashboard"""
    print("[DEBUG] Script started.")
    # Get today's date
    today = datetime.date.today().strftime('%Y-%m-%d')
    print(f"[DEBUG] Today's date: {today}")
    print("[DEBUG] Attempting to open capacity_report.json ...")
    # Load the capacity report
    try:
        with open('capacity_report.json', 'r') as f:
            capacity_data = json.load(f)
        print("[DEBUG] Loaded capacity_report.json successfully.")
    except FileNotFoundError:
        print("[ERROR] capacity_report.json not found!")
        return
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in capacity_report.json! {e}")
        return
    
    # Calculate availability percentage and status data
    ads = list(next(iter(capacity_data.values())).keys())
    availability_percentage, status_data = calculate_availability_data(capacity_data, ads)
    
    # Check if we have data for today, if not use the first available date
    if today in capacity_data:
        target_date = today
        data = capacity_data[today]
        print(f"[DEBUG] Using data for today: {target_date}")
    else:
        # Use the first available date (in this case 2025-07-14)
        available_dates = list(capacity_data.keys())
        if available_dates:
            target_date = available_dates[0]
            data = capacity_data[target_date]
            print(f"Warning: No data for today ({today}). Using data from {target_date}")
        else:
            print("Error: No data found in capacity_report.json!")
            return
    # Generate the HTML
    print("[DEBUG] Generating HTML content...")
    html_content = generate_html(data, target_date, availability_percentage, status_data)
    print("[DEBUG] HTML content generated.")
    # Write to file
    output_file = f"ocvs_availability_{target_date}.html"
    print(f"[DEBUG] Writing HTML to {output_file} ...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Availability dashboard generated successfully!")
    print(f"📄 Output file: {output_file}")
    
    # Also save as index.html
    index_file = "index.html"
    print(f"[DEBUG] Writing HTML to {index_file} ...")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"📄 Output file: {index_file}")
    print(f"📅 Data date: {target_date}")
    print(f"🌐 Open {output_file} or {index_file} in your web browser to view the dashboard")

if __name__ == "__main__":
    main() 