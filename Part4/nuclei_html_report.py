import json
import os
import re

def convert_nuclei_to_html(HOST_REPORTS_PATH: str):
    # חיפוש קובץ ה-JSON בתיקייה שמתחיל ב-nuclei ומסתיים ב-.json
    json_filename = None
    for filename in os.listdir(HOST_REPORTS_PATH):
        if re.match(r'^nuclei.*\.json$', filename):
            json_filename = filename
            break
            
    if not json_filename:
        print("[-] לא נמצא קובץ JSON של Nuclei בתיקייה.")
        return

    # הגדרת הנתיבים המלאים
    json_path = os.path.join(HOST_REPORTS_PATH, json_filename)
    html_filename = re.sub(r'\.json$', '.html', json_filename)
    html_path = os.path.join(HOST_REPORTS_PATH, html_filename)

    findings = []
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #333; color: white; }
            .critical { background-color: #ffcccc; }
            .high { background-color: #ffebcc; }
            .medium { background-color: #ffffcc; }
            .low { background-color: #e6ffcc; }
            .info { background-color: #e6f2ff; }
        </style>
    </head>
    <body>
        <h2>Nuclei Scan Report</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Vulnerability Name</th>
                <th>Target / URL</th>
            </tr>
    """

    for item in findings:
        info = item.get('info', {})
        severity = info.get('severity', 'info').lower()
        name = info.get('name', 'Unknown')
        target = item.get('host', item.get('matched-at', 'Unknown'))

        html_content += f"""
            <tr class="{severity}">
                <td><strong>{severity.upper()}</strong></td>
                <td>{name}</td>
                <td><a href="{target}" target="_blank">{target}</a></td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"[+] הקובץ הומר ונשמר בהצלחה: {html_path}")