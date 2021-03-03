#!/usr/bin/env python3
#
# Copyright (C) 2023 Juergen Kellerer
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
# Converts additional values from `sysctl -a` to prometheus metrics
#

### TODO: Support more metrics

# Prometheus metrics prefix
prom_prefix = "node_hwmon"

# Load sysctl vars and parse lines
sysctl_map = {}
sysctl = subprocess.run(['sysctl', '-a'], capture_output=True)

if sysctl.returncode == 0:
    sysctl_text = sysctl.stdout.decode('utf8', errors='replace')

    ### lines are formatted like (uncomment to test locally):
    #sysctl_text = """
    #dev.cpu.1.temperature: 50
    #hw.acpi.thermal.tz0.temperature: 50.1C
    #hw.acpi.thermal.tz1.temperature: 300
    #hw.temperature.CPU: 50
    #"""

    expression = r'^\s*' \
                 + r'(dev.cpu.(?P<cpu_num>\d+).temperature' \
                 + r'|hw.acpi.thermal.tz(?P<zone_num>\d+).temperature' \
                 + r'|hw.temperature.CPU):\s*' \
                 + r'(?P<temp>[\d\.]+)(?P<celsius>C)?' \
                 + r'\s*$'

    pattern = re.compile(expression)
    matches = filter(lambda m: m is not None,
                     map(pattern.fullmatch, sysctl_text.splitlines()))

    for m in matches:
        temperature = float(m.group('temp'))
        if not temperature:
            continue

        if not m.group('celsius') and m.group('zone_num'):
            temperature -= 273.15 # kelvin to celsius

        if n := m.group('cpu_num'):
            sysctl_map[f'platform_coretemp_0:{n}'] = temperature
        elif n := m.group('zone_num'):
            sysctl_map[f'acpitz:{n}'] = temperature
        else:
            sysctl_map['platform_coretemp_0:0'] = temperature

# Convert to prometheus metrics
metric = f'{prom_prefix}_temp_celsius'
print(f"# HELP {metric} sysctl temperature values in celsius")
print(f"# TYPE {metric} gauge")

for name in sorted(sysctl_map):
    value = sysctl_map[name]
    chip, sensor = str(name).split(':')
    instance = '{chip="%s", sensor="temp%s"}' % (chip, int(sensor)+1)

    print(f"{metric}{instance} {value}")
