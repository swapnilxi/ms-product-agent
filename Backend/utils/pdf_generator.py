# utils/pdf_generator.py
from fpdf import FPDF
import re
import os
from datetime import datetime

def extract_dashboard_content(messages):
    """
    Extract the final dashboard agent's content from the chat messages.
    
    Args:
        messages (list): List of messages from the chat
    
    Returns:
        str: The content from the Dashboard agent, excluding the approval phrase
    """
    dashboard_content = ""
    
    # First try to find the dashboard content in a structured way
    for message in reversed(messages):
        # Handle objects with attributes
        if hasattr(message, 'content') and isinstance(message.content, str):
            content = message.content
            
            # Check if this message contains dashboard agent content
            if 'DashboardAgent' in content and 'This concludes our analysis. APPROVE' in content:
                # Try to extract content between agent name and approval phrase
                try:
                    # Find where the dashboard agent's content starts
                    start_idx = content.find('DashboardAgent')
                    if start_idx >= 0:
                        # Find the colon after agent name
                        colon_idx = content.find(':', start_idx)
                        if colon_idx >= 0:
                            start_idx = colon_idx + 1
                        else:
                            # If no colon, just move past the agent name
                            start_idx += len('DashboardAgent')
                        
                        # Find the end of the content
                        end_idx = content.find('This concludes our analysis. APPROVE', start_idx)
                        if end_idx >= 0:
                            dashboard_content = content[start_idx:end_idx].strip()
                            break
                except Exception as e:
                    print(f"Error extracting dashboard content: {e}")
        
        # Handle dictionary-style messages
        elif isinstance(message, dict):
            content = message.get('content', '')
            if 'DashboardAgent' in content and 'This concludes our analysis. APPROVE' in content:
                parts = content.split('DashboardAgent')
                if len(parts) > 1:
                    # Get content after agent name
                    agent_content = parts[1]
                    # Remove content after approval phrase
                    dashboard_content = agent_content.split('This concludes our analysis. APPROVE')[0].strip()
                    # Remove leading colon if present
                    if dashboard_content.startswith(':'):
                        dashboard_content = dashboard_content[1:].strip()
                    break
    
    # If we still don't have content, try a more aggressive approach
    if not dashboard_content:
        # Combine all messages into a single string
        all_content = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                all_content += str(msg.content) + "\n"
            elif isinstance(msg, dict) and 'content' in msg:
                all_content += str(msg['content']) + "\n"
            elif isinstance(msg, str):
                all_content += msg + "\n"
        
        # Use regex to find the dashboard content
        match = re.search(
            r'DashboardAgent:?\s*(.*?)This concludes our analysis\. APPROVE', 
            all_content, 
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            dashboard_content = match.group(1).strip()
    
    return dashboard_content

def save_to_pdf(content, output_path=None):
    """
    Save the provided content to a PDF file.
    
    Args:
        content (str): The content to save to PDF
        output_path (str, optional): Path where to save the PDF. If None, a default name will be used.
    
    Returns:
        str: Path to the saved PDF file
    """
    if not content:
        print("Warning: No content provided to save to PDF")
        return None
        
    if output_path is None:
        # Create a default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Microsoft_Samsung_Collaboration_{timestamp}.pdf"
    
    # Create PDF instance
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Microsoft-Samsung Collaboration Dashboard", ln=True, align='C')
    pdf.ln(10)
    
    # Add timestamp
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    # Add content
    pdf.set_font("Arial", "", 12)
    
    # Clean content - remove any markdown code blocks
    content = re.sub(r'```[a-zA-Z]*\n', '', content)
    content = re.sub(r'```', '', content)
    
    # Split content by lines and add them to PDF
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            # Check if line is a heading (all caps, ends with :, or starts with #)
            if (line.strip().isupper() or 
                line.strip().endswith(':') or 
                re.match(r'^#+\s', line.strip())):
                
                # Remove markdown heading symbols
                clean_line = re.sub(r'^#+\s', '', line.strip())
                
                pdf.set_font("Arial", "B", 14)
                pdf.ln(5)
                pdf.cell(0, 10, clean_line, ln=True)
                pdf.set_font("Arial", "", 12)
            
            # Check if line is a bullet point
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                pdf.cell(10, 10, "•", ln=0)
                pdf.multi_cell(0, 10, line.strip()[2:])
            
            # Normal line
            else:
                pdf.multi_cell(0, 10, line)
                pdf.ln(2)
    
    # Save PDF
    try:
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return None

def capture_and_save_dashboard_output(messages):
    """
    Main function to extract dashboard content from messages and save to PDF.
    
    Args:
        messages (list): List of messages from the chat
    
    Returns:
        str: Path to the saved PDF file
    """
    dashboard_content = extract_dashboard_content(messages)
    
    if dashboard_content:
        # Create 'reports' directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        
        # Create file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/Microsoft_Samsung_Collaboration_{timestamp}.pdf"
        
        # Save to PDF
        pdf_path = save_to_pdf(dashboard_content, output_path)
        if pdf_path:
            print(f"Dashboard output saved to {pdf_path}")
            return pdf_path
        else:
            print("Failed to save PDF.")
            return None
    else:
        print("No dashboard content found to save.")
        return None

# For direct debugging
if __name__ == "__main__":
    # Example usage for testing
    test_message = """DashboardAgent: Here's the dashboard for tracking Microsoft-Samsung collaboration.

KEY PERFORMANCE INDICATORS:
- Market Penetration Rate
- Monthly Active Users
- Revenue Growth
- Customer Satisfaction Score

This concludes our analysis. APPROVE"""
    
    # Create test message structure
    class TestMessage:
        def __init__(self, content):
            self.content = content
    
    test_obj = TestMessage(test_message)
    pdf_path = capture_and_save_dashboard_output([test_obj])
    print(f"Test PDF saved to: {pdf_path}")