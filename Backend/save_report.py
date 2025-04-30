import os
from datetime import datetime

def save_pipeline_report(results: dict, report_folder="reports"):
    os.makedirs(report_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_md = f"pipeline_report_{timestamp}.md"
    filepath_md = os.path.join(report_folder, filename_md)

    # Build Markdown content
    md_content = "# 📝 Pipeline Report\n\n"
    md_content += f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for key, value in results.items():
        md_content += f"## {key.replace('_', ' ').title()}\n\n"
        md_content += f"{value}\n\n---\n\n"

    # Save .md file
    with open(filepath_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Markdown saved at: {filepath_md}")
    return filename_md

def list_reports(report_folder="reports"):
    os.makedirs(report_folder, exist_ok=True)
    return [f for f in os.listdir(report_folder) if f.endswith(".md")]

def get_report_path(filename, report_folder="reports"):
    filepath = os.path.join(report_folder, filename)
    return filepath if os.path.exists(filepath) else None

def delete_report(filename, report_folder="reports"):
    filepath = os.path.join(report_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
