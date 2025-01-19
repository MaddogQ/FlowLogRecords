# Flow Log Parser

A command line tool written in Python to parse [flow logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html) and map them to tags.

## Assumptions

1. Input files (flow logs and lookup table) are plain text (ASCII) files.
2. The lookup table is defined as a csv file, and it has 3 columns, **dstport**, **protocol**, and **tag**.
3. The flow log is in default format, version 2 only. Custom format is currently not supported.
4. Matches for ports and protocols are case-insensitive.
5. The program handles flow logs up to 10 MB.
6. The program handles lookup table sizes up to 10,000 entries.
7. Tags can be associated with multiple port and protocol combinations. For instance, in the sample above, both `sv_P1` and `sv_P2` apply to different combinations.

## Usage

Input: lookup table, flow log file

Output: Count of matches for each tag, count of matches for each port/protocol combination

```bash
flow_log_parser.py [-h] [-l LOOKUP] [-f LOG] [-V] [-v]
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

## Analysis
