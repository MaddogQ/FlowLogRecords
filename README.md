# Flow Log Parser

## Assumptions:

1. The program supports only default flow log format and version 2, not custom format.
2. Input files (flow logs and lookup table) are plain text (ASCII) files.
3. Matches for ports and protocols are case-insensitive.
4. The program handles flow logs up to 10 MB.
5. The program handles lookup table sizes up to 10,000 entries.
6. Tags can be associated with multiple port and protocol combinations. For instance, in the sample above, both `sv_P1` and `sv_P2` apply to different combinations.

## How to Run:

1. Run the program (using python 3.10+):
   ```bash
   python flow_log_parser.py
   ```

## Testing:

## Analysis:
