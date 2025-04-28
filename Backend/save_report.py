# save_report.py
import os
from datetime import datetime

def save_pipeline_report(results: dict, report_folder="reports"):
    # Create reports folder if it doesn't exist
    os.makedirs(report_folder, exist_ok=True)

    # Timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pipeline_report_{timestamp}.md"
    filepath = os.path.join(report_folder, filename)

    # Build Markdown content
    md_content = "# 📝 Pipeline Report\n\n"
    md_content += f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for key, value in results.items():
        md_content += f"## {key.replace('_', ' ').title()}\n\n"
        md_content += f"{value}\n\n---\n\n"

    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    return filepath

# List all report files
def list_reports(report_folder="reports"):
    os.makedirs(report_folder, exist_ok=True)
    files = [f for f in os.listdir(report_folder) if f.endswith(".md")]
    return files

# Get full path for a specific report
def get_report_path(filename, report_folder="reports"):
    filepath = os.path.join(report_folder, filename)
    if os.path.exists(filepath):
        return filepath
    else:
        return None
# Delete a specific report  
def delete_report(filename, report_folder="reports"):
    filepath = os.path.join(report_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    else:
        return False
