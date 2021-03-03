#!/usr/local/bin/php
<?php
/*
 * Copyright (C) 2021 Juergen Kellerer
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *  1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 * AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

use OPNsense\NodeExporter\General;

// Try to get a lock on General::NODE_EXPORTER_TEXTFILE_DIR
$locked = (function () {
    $locked = false;
    $lock_file = fopen(General::NODE_EXPORTER_TEXTFILE_DIR . "/.lock", 'w+');

    if (is_resource($lock_file)) {
        $locked = flock($lock_file, LOCK_EX);

        register_shutdown_function(function () use ($lock_file, $locked) {
            if ($locked) {
                flock($lock_file, LOCK_UN);
            }
            fclose($lock_file);
            @unlink($lock_file);
        });
    }

    return $locked;
})();

// Check lock
if (!$locked) {
    echo "Failed to get a lock on " . General::NODE_EXPORTER_TEXTFILE_DIR;
    exit(1);
}

// Try to get existing links
$existing_links = (function () {
    $links = false;
    $directory = dir(General::NODE_EXPORTER_TEXTFILE_DIR);

    if (is_object($directory)) {
        $links = [];
        while (false !== ($name = $directory->read())) {
            if (is_link($name) && preg_match('/.+\.prom/', $name)) {
                $links[] = $name;
            }
        }
    }

    return $links;
})();

# Check if link folder can be scanned
if ($existing_links === false) {
    echo "Failed to read links from " . General::NODE_EXPORTER_TEXTFILE_DIR;
    exit(1);
}

# Getting expected links from config
$expected_links = (function () {
    $links = [];

    // Reading enabled prom file names
    $model = new General();
    foreach ($model->file_collector->iterateItems() as $entry) {
        if ((bool)$entry->enabled) {
            $links[] = (string)$entry->name;
        }
    }

    return $links;
})();

// Applying changes
(function () use ($existing_links, $expected_links) {
    $links_to_add = array_diff($expected_links, $existing_links);
    $links_to_remove = array_diff($existing_links, $expected_links);

    foreach ($links_to_remove as $name) {
        $link = General::NODE_EXPORTER_TEXTFILE_DIR . "/$name";
        $ok = unlink($link);

        if (!$ok) {
            // TODO: Log
            echo "Failed unlink $link";
        }
    }

    foreach ($links_to_add as $name) {
        $target = General::NODE_EXPORTER_TEXTFILE_WORKDIR . "/$name";
        $link = General::NODE_EXPORTER_TEXTFILE_DIR . "/$name";
        $ok = link($target, $link);

        if (!$ok) {
            // TODO: Log
            echo "Failed to link $link to $target";
        }
    }
})();
