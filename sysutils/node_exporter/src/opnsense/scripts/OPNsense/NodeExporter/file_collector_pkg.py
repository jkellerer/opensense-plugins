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
# Converts "/usr/sbin/pkg upgrade" information to prometheus metrics (similar to apt and yum collector scripts)
#

# Load pending package counts into stats
stats = {'__all': 0, 'removed': 0, 'upgraded': 0, 'installed': 0, 'reinstalled': 0}

pkg_upgrade = subprocess.run(["/usr/sbin/pkg", "upgrade", "--dry-run"],
                             capture_output=True)

output_text = pkg_upgrade.stdout.decode('utf8', errors='replace')

pattern = re.compile('Number of packages to be (upgraded|installed|reinstalled|removed): ([0-9]+)$')
matches = filter(lambda m: m is not None,
                 map(pattern.fullmatch, output_text.splitlines()))

for m in matches:
    stats[m.group(1)] = int(m.group(2))

new_pkg = 'New version of pkg detected'
if new_pkg in output_text:
    stats['upgraded'] += 1

# Create metrics
stats['__all'] = sum(stats.values())

print('# HELP pkg_pending pkg packages pending upgrade, (re)installation or removal.')
print('# TYPE pkg_pending gauge')
print(f"pkg_pending {stats['__all']}")

print('# HELP pkg_upgrades_pending pkg packages pending upgrade.')
print('# TYPE pkg_upgrades_pending gauge')
print(f"pkg_upgrades_pending {stats['upgraded']}")

print('# HELP pkg_installation_pending pkg packages pending installation.')
print('# TYPE pkg_installation_pending gauge')
print(f"pkg_installation_pending {stats['installed']}")

print('# HELP pkg_reinstallation_pending pkg packages pending reinstallation.')
print('# TYPE pkg_reinstallation_pending gauge')
print(f"pkg_reinstallation_pending {stats['reinstalled']}")

print('# HELP pkg_removals_pending pkg packages pending removal.')
print('# TYPE pkg_removals_pending gauge')
print(f"pkg_removals_pending {stats['removed']}")
