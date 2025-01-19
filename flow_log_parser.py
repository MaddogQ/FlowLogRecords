import argparse
import csv
import os
from collections import Counter, defaultdict

# Ref: https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_MAP = {
    1: "icmp",
    6: "tcp",
    17: "udp",
}  # Map of protocol numbers to actual protocol names, currently only ICMP, TCP and UDP are supported

# Ref: https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html
NUM_FIELDS = 14  # Number of fields in the flow log file


# Function to load lookup table
def load_lookup_table(lookup_file):
    lookup = {}
    try:
        with open(lookup_file, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if len(row) == 3:
                    port, protocol, tag = row
                    lookup[(port.strip(), protocol.strip())] = tag.strip()
    except Exception as e:
        print(f"Error reading lookup file: {e}")
    return lookup


# Function to parse flow logs and map to tags
def parse_flow_logs(log_file, lookup, verbose=False):
    tag_counts = Counter()
    port_protocol_counts = Counter()
    untagged_count = 0  # for exception handling

    try:
        with open(log_file, "r") as file:
            for line_number, line in enumerate(file, 1):
                parts = line.strip().split()

                if parts == []:  # Skip empty lines
                    continue

                if len(parts) < NUM_FIELDS:
                    print(
                        f"Warning: Malformed data at line {line_number}"
                    )  # Add warning for malformed data
                    continue

                # Get port and protocol
                dstport, protocol = parts[6].strip(), parts[7].strip()
                # Convert protocol to actual protocol name
                protocol = PROTOCOL_MAP.get(int(protocol), "Unknown")

                key = (dstport, protocol)

                # Match with lookup table
                if key in lookup:
                    if verbose:
                        print(f"Found tag for {key}: {lookup[key]}")
                    tag = lookup[key]
                    tag_counts[tag] += 1
                else:
                    tag = "Untagged"
                    untagged_count += 1

                port_protocol_counts[key] += 1

        tag_counts["Untagged"] = untagged_count

    except Exception as e:
        print(f"Error reading log file: {e}")
        raise  # Error handling

    return tag_counts, port_protocol_counts


# Function to write output files
def write_output_files(tag_counts, port_protocol_counts):
    try:
        # Sort the results for better readability
        sorted_tags = dict(sorted(tag_counts.items()))
        sorted_ports = dict(sorted(port_protocol_counts.items()))

        with open("tag_counts.csv", "w", newline="") as tag_file:
            writer = csv.writer(tag_file)
            writer.writerow(["Tag", "Count"])
            for tag, count in sorted_tags.items():
                writer.writerow([tag, count])

        with open("port_protocol_counts.csv", "w", newline="") as port_file:
            writer = csv.writer(port_file)
            writer.writerow(["Port", "Protocol", "Count"])
            for (port, protocol), count in sorted_ports.items():
                writer.writerow([port, protocol, count])

    except Exception as e:
        print(f"Error writing output files: {e}")
        raise  # Error handling


# Main function
def main():
    # Parsing arguments
    parser = argparse.ArgumentParser(
        description="Parse flow logs and map them to tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
python flow_log_parser.py                              # Run with default files
python flow_log_parser.py -h                           # Show help
python flow_log_parser.py -l custom_lookup.csv         # Use custom lookup file
python flow_log_parser.py --log custom_flow.txt        # Use custom log file
python flow_log_parser.py -V                           # Run with verbose output
""",
    )

    # Required arguments group
    input_group = parser.add_argument_group("Input/Output Options")
    input_group.add_argument(
        "-l",
        "--lookup",
        default="lookup_table.csv",
        help="Path to the lookup table CSV file (default: lookup_table.csv)",
    )
    input_group.add_argument(
        "-f",
        "--log",
        default="flow_log.txt",
        help="Path to the flow log file (default: flow_log.txt)",
    )

    # Optional arguments
    parser.add_argument(
        "-V", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 1.0",
        help="Show program version",
    )

    args = parser.parse_args()

    # Check if lookup file and flow log file exist
    if not os.path.exists(args.lookup):
        parser.error("Lookup file does not exist.")
    if not os.path.exists(args.log):
        parser.error("Flow log file does not exist.")

    if args.verbose:
        print(f"Processing lookup file: {args.lookup}")
        print(f"Processing log file: {args.log}")
        print()

    lookup = load_lookup_table(args.lookup)
    tag_counts, port_protocol_counts = parse_flow_logs(args.log, lookup, args.verbose)

    if args.verbose:
        print(tag_counts)
        print(port_protocol_counts)

    write_output_files(tag_counts, port_protocol_counts)

    if args.verbose:
        print("\nProcessing statistics:")
        print(f"Total tags processed: {sum(tag_counts.values())}")
        print(f"Unique port/protocol combinations: {len(port_protocol_counts)}")

    print(
        "Processing complete. Outputs saved as tag_counts.csv and port_protocol_counts.csv"
    )


if __name__ == "__main__":
    main()
