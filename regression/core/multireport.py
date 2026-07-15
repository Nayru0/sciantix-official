"""
sciantix regression suite
author: Giovanni Zullo
"""

import os
import datetime

def generate_html_multireport(results, phy_quantities, output_dir):
    """
    Generate an HTML report for regression results.
    
    Args:
        results: list of tuples (test_name, [ok,...,ok], message) (there is an ok for each physical quantity being tested)
        phy_quantities: list of physical quantities being tested
        output_dir: directory to save index.html
    """
    
    passed = sum(r[1].count(True) for r in results)
    failed = len(results)*len(phy_quantities) - passed
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SCIANTIX Regression Report</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ margin-bottom: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .pass {{ color: green; font-weight: bold; }}
            .fail {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>SCIANTIX Regression Report</h1>
        
        <div class="summary">
            <p><strong>Date:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p><strong>Total Tests:</strong> {len(results)*len(phy_quantities)}</p>
            <p><strong>Passed:</strong> <span class="pass">{passed}</span></p>
            <p><strong>Failed:</strong> <span class="fail">{failed}</span></p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Test Case</th>"""
    for phy_quantity in phy_quantities:
        html += f"""
                        <th>Status - {phy_quantity}</th>
        """
    html += f"""
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for name, ok_list, msg in results:
        message = msg if msg else ""
        
        html += f"""
                <tr>
                    <td>{name}</td>
        """
        for ok in ok_list:
            status_class = "pass" if ok else "fail"
            status_text = "PASS" if ok else "FAIL"
            html += f"""
                    <td class="{status_class}">{status_text}</td>
            """
        html += f"""
                    <td>{message}</td>
                </tr>
        """
        
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    report_path = os.path.join(output_dir, "multireport.html")
    with open(report_path, "w") as f:
        f.write(html)
        
    print(f"\nReport generated: {report_path}")
