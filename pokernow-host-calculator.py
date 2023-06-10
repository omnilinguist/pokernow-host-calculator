import csv
from datetime import datetime
import re
import sys

# Methodology:
#
# Infer table start/end times by start of first hand / end of last hand
#
# Find inflection points by (example: 'The player ""John Smith @ DEADBEEF"" passed the room ownership to ""Jane Doe @ BEEFDEAD"".",2023-06-09T12:28:18.393Z,168631369839300') and marshal them into temporary rows, ie:
# T0, -, -
# T1, A, B
# T2, B, C
# T3, C, D
# T4, -, -
#
# Convert these into hosted duration segments, ie:
# T0, T1, A
# T1, T2, B
# T2, T3, C
# T3, T4, D
#
# Calculate what portion of total duration each segment comprised and print

def run():
  if len(sys.argv) < 2:
    return
  log_csv = sys.argv[1]
  with open(log_csv, 'r') as file:
    csvreader = csv.reader(file)

    ts_start = None
    ts_end = None
    inflections = []
    for entry, ts, order  in csvreader:
      if ts == 'at':
        continue  # hack to skip 1st line
      if ts.endswith('Z'):
        ts = ts[:-1]  # hack to workaround datetime native limitation in order to not require installing 3rd party dateutil library
      ts_parsed = datetime.fromisoformat(ts)

      if 'ending hand' in entry and not ts_end:  # end time
        ts_end = ts_parsed
      if 'starting hand #1 ' in entry and not ts_start:  # start time
        ts_start = ts_parsed
      if 'passed the room ownership' in entry:
        result = re.search(r'.*"(.*)".*"(.*)"', entry)
        owner_old = result[1]
        owner_new = result[2]
        inflections.append([ts_parsed, owner_old, owner_new])
        #print(entry, ts, ts_parsed, owner_old, owner_new)
      pass
    if len(inflections) == 0:
      print('No host changes during game')
      return
    inflections.sort(key=lambda x: x[0])
   
    host_segments = []
    ts_prev = ts_start
    for i in inflections:
      host_segments.append([ts_prev, i[0], i[1]])
      ts_prev = i[0]
    host_segments.append([inflections[-1][0], ts_end, inflections[-1][2]])

    time_total = ts_end - ts_start
    print('total time: {}'.format(time_total))
    for s in host_segments:
      time_segment = s[1] - s[0]
      print('{} was host from {} to {} (UTC): {} ({:.4%})'.format(s[2], str(s[0]), str(s[1]), time_segment, time_segment / time_total))

if __name__ == '__main__':
  run()
