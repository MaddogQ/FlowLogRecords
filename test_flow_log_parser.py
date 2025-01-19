import os
import tempfile
import time
import unittest

from flow_log_parser import load_lookup_table, parse_flow_logs, write_output_file


# Helper function to generate a large lookup table
def generate_large_lookup_file():
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

    # Write header
    temp_file.write("port,protocol,tag\n")

    # Generate many port/protocol combinations
    for port in range(10000):  # According to assumption
        temp_file.write(f"{port},tcp,tcp-traffic-{port}\n")
        temp_file.write(f"{port},udp,udp-traffic-{port}\n")

    temp_file.close()
    return temp_file.name


# Helper function to generate a large flow log
def generate_large_flow_log():
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

    # Generate many flow log entries
    for i in range(100000):  # According to assumption
        port = (i % 10000) + 1
        protocol = 6 if i % 2 == 0 else 17  # Alternate between TCP (6) and UDP (17)
        temp_file.write(
            f"2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 {port} {protocol} 100 1000 1234567890 1234567899 ACCEPT OK\n"
        )

    temp_file.close()
    return temp_file.name


class TestFlowLogParser(unittest.TestCase):
    def setUp(self):
        # Create temporary test files
        self.lookup_data = """port,protocol,tag
80,tcp,web-traffic
443,tcp,secure-web
53,udp,dns
"""
        self.flow_log_data = """2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 80 6 100 1000 1234567890 1234567899 ACCEPT OK
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 443 6 100 1000 1234567890 1234567899 ACCEPT OK
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 53 17 100 1000 1234567890 1234567899 ACCEPT OK
"""
        # Create temporary files
        self.lookup_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        self.flow_log_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        self.output_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

        self.lookup_file.write(self.lookup_data)
        self.flow_log_file.write(self.flow_log_data)

        self.lookup_file.close()
        self.flow_log_file.close()
        self.output_file.close()

    def tearDown(self):
        # Clean up temporary files
        os.unlink(self.lookup_file.name)
        os.unlink(self.flow_log_file.name)
        os.unlink(self.output_file.name)

    def test_load_lookup_table(self):
        lookup = load_lookup_table(self.lookup_file.name)
        self.assertEqual(lookup[("80", "tcp")], "web-traffic")
        self.assertEqual(lookup[("443", "tcp")], "secure-web")
        self.assertEqual(lookup[("53", "udp")], "dns")

    def test_parse_flow_logs(self):
        lookup = load_lookup_table(self.lookup_file.name)
        tag_counts, port_protocol_counts = parse_flow_logs(
            self.flow_log_file.name, lookup
        )

        # Test tag counts
        self.assertEqual(tag_counts["web-traffic"], 1)
        self.assertEqual(tag_counts["secure-web"], 1)
        self.assertEqual(tag_counts["dns"], 1)

        # Test port/protocol counts
        self.assertEqual(port_protocol_counts[("80", "tcp")], 1)
        self.assertEqual(port_protocol_counts[("443", "tcp")], 1)
        self.assertEqual(port_protocol_counts[("53", "udp")], 1)

    def test_write_output_file(self):
        lookup = load_lookup_table(self.lookup_file.name)
        tag_counts, port_protocol_counts = parse_flow_logs(
            self.flow_log_file.name, lookup
        )
        write_output_file(self.output_file.name, tag_counts, port_protocol_counts)

        # Verify file was created and is not empty
        self.assertTrue(os.path.exists(self.output_file.name))
        self.assertGreater(os.path.getsize(self.output_file.name), 0)

    def test_performance(self):
        # Generate large test files
        large_lookup = generate_large_lookup_file()
        large_flow_log = generate_large_flow_log()

        start_time = time.time()

        # Run your parsing
        lookup = load_lookup_table(large_lookup)
        tag_counts, port_protocol_counts = parse_flow_logs(large_flow_log, lookup)

        execution_time = time.time() - start_time
        print(f"Processing time: {execution_time} seconds")

        # Clean up temporary files
        os.unlink(large_lookup)
        os.unlink(large_flow_log)

    def test_empty_files(self):
        # Create empty files
        empty_lookup = tempfile.NamedTemporaryFile(mode="w", delete=False)
        empty_flow = tempfile.NamedTemporaryFile(mode="w", delete=False)

        empty_lookup.write("port,protocol,tag\n")  # Only header
        empty_lookup.close()
        empty_flow.close()

        # Test empty lookup table
        lookup = load_lookup_table(empty_lookup.name)
        self.assertEqual(len(lookup), 0)

        # Test empty flow log
        tag_counts, port_protocol_counts = parse_flow_logs(empty_flow.name, lookup)
        self.assertEqual(len(tag_counts), 1)  # Should only have "Untagged"
        self.assertEqual(len(port_protocol_counts), 0)

        # Cleanup
        os.unlink(empty_lookup.name)
        os.unlink(empty_flow.name)

    def test_malformed_lookup_data(self):
        malformed_lookup = tempfile.NamedTemporaryFile(mode="w", delete=False)
        malformed_lookup.write(
            """port,protocol,tag
80,tcp,web-traffic
invalid_line
443,tcp,secure-web,extra_field
,,,
53,udp,dns
"""
        )
        malformed_lookup.close()

        lookup = load_lookup_table(malformed_lookup.name)
        self.assertEqual(len(lookup), 2)  # Should only load valid lines
        self.assertIn(("80", "tcp"), lookup)
        self.assertIn(("53", "udp"), lookup)

        os.unlink(malformed_lookup.name)

    def test_malformed_flow_logs(self):
        malformed_flow = tempfile.NamedTemporaryFile(mode="w", delete=False)
        malformed_flow.write(
            """
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 80 6 100 1000 1234567890 1234567899 ACCEPT OK
invalid line
2 123456789 eni-abc123 10.0.0.1
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 443 999999 100 1000 1234567890 1234567899 ACCEPT OK
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 53 17 100 1000 1234567890 1234567899 ACCEPT OK
"""
        )
        malformed_flow.close()

        lookup = load_lookup_table(self.lookup_file.name)

        tag_counts, port_protocol_counts = parse_flow_logs(malformed_flow.name, lookup)

        # Should only process valid lines
        self.assertEqual(tag_counts["web-traffic"], 1)
        self.assertEqual(tag_counts["dns"], 1)
        self.assertEqual(
            tag_counts["Untagged"], 1
        )  # For the line with invalid protocol

        os.unlink(malformed_flow.name)

    def test_invalid_protocols(self):
        invalid_protocol_flow = tempfile.NamedTemporaryFile(mode="w", delete=False)
        invalid_protocol_flow.write(
            """
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 80 999 100 1000 1234567890 1234567899 ACCEPT OK
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 443 -1 100 1000 1234567890 1234567899 ACCEPT OK
2 123456789 eni-abc123 10.0.0.1 10.0.0.2 12345 53 abc 100 1000 1234567890 1234567899 ACCEPT OK
"""
        )
        invalid_protocol_flow.close()

        lookup = load_lookup_table(self.lookup_file.name)
        tag_counts, port_protocol_counts = parse_flow_logs(
            invalid_protocol_flow.name, lookup
        )

        # All entries should be untagged due to invalid protocols
        self.assertEqual(tag_counts["Untagged"], 3)

        os.unlink(invalid_protocol_flow.name)

    def test_duplicate_entries(self):
        duplicate_lookup = tempfile.NamedTemporaryFile(mode="w", delete=False)
        duplicate_lookup.write(
            """port,protocol,tag
80,tcp,web-traffic-1
80,tcp,web-traffic-2
443,tcp,secure-web
53,udp,dns-1
53,udp,dns-2
"""
        )
        duplicate_lookup.close()

        lookup = load_lookup_table(duplicate_lookup.name)
        # Last entry should win for duplicates
        self.assertEqual(lookup[("80", "tcp")], "web-traffic-2")
        self.assertEqual(lookup[("53", "udp")], "dns-2")

        os.unlink(duplicate_lookup.name)


if __name__ == "__main__":
    unittest.main()
