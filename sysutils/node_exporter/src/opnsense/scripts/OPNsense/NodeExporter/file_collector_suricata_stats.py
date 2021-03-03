#!/usr/bin/env python3
#
# Copyright (C) 2021 Juergen Kellerer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import re
import subprocess

#
# Converts /var/log/suricata/stats.log to prometheus metrics
#

# Prometheus metrics prefix
prom_prefix = "suricata_stats"

# Source and number of lines to look for latest stats
stats_file = "/var/log/suricata/stats.log"
tail_lines = 200

# Load latest suricata stats into env as "__prom_suricata_data_*=numeric_value"
# Lines are formatted like:
#   app_layer.flow.failed_tcp    | Total    | 8704
#   app_layer.flow.dcerpc_udp    | Total    | 2
stats_map = {}

stats = subprocess.run(["tail", "--lines", str(tail_lines), str(stats_file)],
                       capture_output=True)

if stats.returncode == 0:
    stats_text = stats.stdout.decode('utf8', errors='replace')

    pattern = re.compile('^([a-z_.]+)[ ]+\\| Total[ ]+\\| ([0-9]+)[ ]*$')
    matches = filter(lambda m: m is not None,
                     map(pattern.fullmatch, stats_text.splitlines()))

    for m in matches:
        key = m.group(1)
        stats_map[key.replace('.', '_')] = m.group(2)

# Convert "__prom_suricata_data_*" env to prometheus metrics
for name in sorted(stats_map):
    value = stats_map[name]
    type = "gauge"
    metric = "%s_%s_total" % (prom_prefix, name)

    if "memuse" in name:
        metric = "%s_%s_bytes" % (prom_prefix, name)
    elif "session" in name:
        type = "gauge"
    else:
        type = "counter"

    print(f"# HELP {metric} suricata stats total for {name}")
    print(f"# TYPE {metric} {type}")
    print(f"{metric} {value}")
