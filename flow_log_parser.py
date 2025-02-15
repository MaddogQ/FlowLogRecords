import argparse
import csv
import os
from collections import Counter

# Ref: https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_MAP = {
    1: "icmp",
    6: "tcp",
    17: "udp",
}  # Map of protocol numbers to actual protocol names, currently only ICMP, TCP and UDP are supported

# Ref: https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html
NUM_FIELDS = 14  # Number of fields in the flow log file


def load_lookup_table(lookup_file, verbose=False):
    """Loads the lookup table from the given file.

    Args:
        lookup_file (str): The path to the lookup table file.
        verbose (bool, optional): Whether to print verbose output. Defaults to
        False.

    Returns:
        dict: A dictionary with port/protocol combinations as keys and tags as
        values.
    """
    lookup = {}
    try:
        with open(lookup_file, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for line_number, row in enumerate(reader, 1):
                if len(row) == 3:
                    port, protocol, tag = row
                    lookup[(port.strip(), protocol.strip())] = tag.strip()
                elif verbose:
                    print(
                        f"Warning: Malformed lookup data at line {line_number}. Skipping..."
                    )
    except Exception as e:
        print(f"Error reading lookup file: {e}")
        raise  # Error handling
    return lookup


def parse_flow_logs(log_file, lookup, verbose=False):
    """Parses the flow logs and maps them to tags.

    Args:
        log_file (str): The path to the flow log file.
        lookup (dict): A dictionary with port/protocol combinations as keys and
        tags as values.
        verbose (bool, optional): Whether to print verbose output. Defaults to
        False.

    Returns:
        tuple: A tuple containing two dictionaries. 1st contains the tag counts,
        and 2nd contains the port/protocol counts.
    """
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
                    if verbose:
                        print(
                            f"Warning: Malformed log data at line {line_number}. Skipping..."
                        )  # Add warning for malformed data
                    continue

                # Get port and protocol
                dstport, protocol = parts[6].strip(), parts[7].strip()
                try:
                    # Convert protocol to actual protocol name
                    protocol = PROTOCOL_MAP.get(int(protocol), "Unknown")
                except ValueError:  # In case of malformed protocol number
                    protocol = "Unknown"

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


def write_output_file(output_file, tag_counts, port_protocol_counts, reverse=False):
    """Writes the output files.

    Args:
        output_file (str): The path to the output file.
        tag_counts (dict): A dictionary with tags as keys and counts as values.
        port_protocol_counts (dict): A dictionary with port/protocol
        combinations as keys and counts as values.
        reverse (bool, optional): Whether to sort in descending order. Defaults
        to False.
    """
    try:
        # Sort the results for better readability, reverse=True for descending order
        sorted_tags = dict(sorted(tag_counts.items(), reverse=reverse))
        sorted_ports = dict(sorted(port_protocol_counts.items(), reverse=reverse))

        with open(output_file, "w", newline="") as tag_file:
            writer = csv.writer(tag_file)
            writer.writerow(["Tag Counts:"])
            writer.writerow(["Tag", "Count"])
            for tag, count in sorted_tags.items():
                writer.writerow([tag, count])
            writer.writerow([])
            writer.writerow(["Port/Protocol Combination Counts:"])
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
python flow_log_parser.py -o custom_output.csv         # Use custom output file
python flow_log_parser.py -r                           # Sort in descending order
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
    input_group.add_argument(
        "-o",
        "--output",
        default="log_stats.csv",
        help="Path to the output file (default: log_stats.csv)",
    )
    input_group.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Sort in descending order (default: ascending)",
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

    lookup = load_lookup_table(args.lookup, args.verbose)
    tag_counts, port_protocol_counts = parse_flow_logs(args.log, lookup, args.verbose)

    if args.verbose:
        print(tag_counts)
        print(port_protocol_counts)

    write_output_file(args.output, tag_counts, port_protocol_counts, args.reverse)

    if args.verbose:
        print("\nProcessing statistics:")
        print(f"Total tags processed: {sum(tag_counts.values())}")
        print(f"Unique port/protocol combinations: {len(port_protocol_counts)}")

    print("Processing complete. Outputs saved as log_stats.csv")


if __name__ == "__main__":
    main()
