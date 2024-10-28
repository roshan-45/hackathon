import json
def read_log_file(file_path):  # Corrected: use parameter name instead of string
    try:
        log_lines = []
        with open(file_path, 'r') as log_file:
            for line in log_file:
                line = line.strip()  # Remove leading/trailing whitespace
                if line.endswith("\\"):  # Check if line ends with '\'
                    line = line[:-1]  # Remove the '\' at the end
                log_lines.append(line)
        return log_lines
    except Exception as e:
        return f"Error reading log file: {e}"
    
def parse_log_line(log_line):
    # Split the log line into its main parts
    parts = log_line.split('\t')
    # Extract the timestamp, process ID, log level, and message
    if len(parts) >= 5:
        timestamp = parts[0]  # Timestamp
        process_id = parts[1]  # Process ID (0)
        log_level = parts[2]   # Log level (Debug or Error)
        category = parts[3]    # Category or context (Diag)
        details = parts[4]     # Remaining details (e.g., 7881|7878|...)
        return {
            'timestamp': timestamp,
            'process_id': process_id,
            'log_level': log_level,
            'category': category,
            'details': details
        }
    else:
        return None
# Full pipeline: Read the log file, remove '\', and parse each line

def process_log_file(file_path):
    # Read log file and handle backslash at the end of lines
    log_lines = read_log_file(file_path)
    # Parse each log line
    parsed_logs = []
    for line in log_lines:
        parsed_log = parse_log_line(line)
        if parsed_log:
            parsed_logs.append(parsed_log)
    return parsed_logs
# Example usage

log_file_path = 'logFiles/APP01/skully.log'  # Provide the actual path to your log file here
parsed_data = process_log_file(log_file_path)
# Display the parsed data
for entry in parsed_data:
    print(entry)
def save_to_json(parsed_data, output_file):
    with open(output_file, 'w') as f:
        json.dump(parsed_data, f, indent=4)
# Save parsed data to a JSON file
save_to_json(parsed_data, 'parsed_logs.json')