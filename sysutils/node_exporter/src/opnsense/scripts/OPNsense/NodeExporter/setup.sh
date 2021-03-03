#!/bin/sh

# Setup user & group (todo: should be own user)
export node_exporter_user="nobody"
export node_exporter_group="nobody"

#if ! /usr/sbin/pw usershow "${node_exporter_user}" > /dev/null ; then
#  /usr/sbin/pw useradd -d /nonexistent -s /usr/sbin/nologin "${node_exporter_user}"
#fi

# Setup Text Collector paths
export node_exporter_textfile_dir="/var/tmp/node_exporter"
export node_exporter_textfile_workdir="/tmp/node_exporter"

[ -d "${node_exporter_textfile_dir}" ]     || mkdir -p ${node_exporter_textfile_dir}
[ -d "${node_exporter_textfile_workdir}" ] || mkdir -p "${node_exporter_textfile_workdir}"

chown "${node_exporter_user}:${node_exporter_group}" "${node_exporter_textfile_dir}"
chown "root:wheel" "${node_exporter_textfile_workdir}"

chmod 1755 "${node_exporter_textfile_dir}"
chmod 1775 "${node_exporter_textfile_workdir}"

if [ ! -f "${node_exporter_textfile_dir}/.synced" ] ; then
  /usr/local/opnsense/scripts/OPNsense/NodeExporter/sync_file_collector_links.php
fi
