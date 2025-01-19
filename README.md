# Flow Log Parser

A command line tool written in Python to parse [flow logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html) and map them to tags.

## Assumptions

1. Input files (flow logs and lookup table) are plain text (ASCII) files.
2. The lookup table is defined as a csv file. It starts with a header row, and it has 3 columns, **dstport**, **protocol**, and **tag**.
3. The flow log is in default format, version 2 only, without header. Custom format is currently not supported.
4. Matches for ports and protocols are case-insensitive.
5. The program handles flow logs up to 10 MB.
6. The program handles lookup table sizes up to 10,000 entries.
7. Tags can be associated with multiple port and protocol combinations. For instance, in the sample above, both `sv_P1` and `sv_P2` apply to different combinations.

## Usage

Input: lookup table, flow log file

Output: log statistics containing tag counts and port/protocol counts

```bash
flow_log_parser.py [-h] [-l LOOKUP] [-f LOG] [-o OUTPUT] [-r] [-V] [-v]
```

## How to Run

1. Clone the repository.
2. Run the program (using python 3.10+) in the terminal using default arguments:
   ```bash
   python flow_log_parser.py
   ```
   (Lookup table: `lookup_table.csv` and flow log: `flow_log.txt`)
3. Run `python flow_log_parser.py --help` to see the full list of arguments and examples.

## Testing

To run the test, use `python -m unittest test_flow_log_parser.py`.

The following test cases are included:

1. Test with a small lookup table and flow log (basic functionality)
2. Test with a large lookup table and flow log (performance test)
3. Test with empty files (header-only lookup table, empty flow log)
4. Test with malformed lookup data (invalid lines, extra fields, missing fields)
5. Test with malformed flow logs (incomplete entries, invalid format)
6. Test with invalid protocols (invalid numbers, negative values, non-numeric)
7. Test with duplicate entries in lookup table (verifying last entry wins)

## Analysis

Overall Time Complexity: O(n+m), where n is the size of the lookup table, and m is the size of the flow log.

Overall Space Complexity: O(n), where n is the size of the lookup table. (Both ignoring the the number of unique tags and port/protocol combinations)

---

One log entry is ~100 bytes. 10 MB flow log is approximately 100,000 entries.
Therefore, the size bound is:

- Lookup table: n ≤ 10,000 entries
- Flow logs: m ≤ 100,000 entries

Given the size bound, the worst case scenario is 100,000 entries in the flow log and 10,000 entries in the lookup table, which under performance test took 0.290 seconds. The current implementation is quite efficient.

### Potential Improvements (for larger data)

Memory:

1. Process flow logs in chunks to save memory.
2. Use a more efficient data structure for lookup table (e.g., a hash table) to speed up lookups.

Performance:

1. Process flow logs in parallel to speed up the parsing process.
