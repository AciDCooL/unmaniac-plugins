#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from unmanic.libs.unplugins.settings import PluginSettings

from unmanic.libs.system.ffmpeg import Probe, Parser

logger = logging.getLogger("Unmanic.Plugin.acidcool_rename_stream_language_tag")

class Settings(PluginSettings):
    settings = {
        "search_language": "dut",
        "replace_language": "nld",
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "search_language": {
                "label": "Language tag to search for (e.g. dut)",
            },
            "replace_language": {
                "label": "Language tag to replace it with (e.g. nld)",
            },
        }

def get_matching_streams(probe_streams, search_language):
    """
    Returns a list of stream indices that match the search language.
    """
    matching_indices = []
    for stream in probe_streams:
        if "tags" in stream and "language" in stream["tags"]:
            if stream["tags"]["language"].lower() == search_language.lower():
                matching_indices.append(stream["index"])
    return matching_indices

def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.
    """
    abspath = data.get('path')

    try:
        from unmanic.libs.system.ffmpeg import Probe
    except ImportError:
        # If running from a v2 environment where path is different, we handle it
        pass

    # Since Probe import might vary, we can just use the provided data if available,
    # or instantiate Probe dynamically.
    probe_data = Probe(logger, allowed_mimetypes=['audio', 'video'])
    if 'ffprobe' in data.get('shared_info', {}):
        if not probe_data.set_probe(data.get('shared_info', {}).get('ffprobe')):
            return data
    elif not probe_data.file(abspath):
        logger.debug("Probe data failed - Blocking everything.")
        data['add_file_to_pending_tasks'] = False
        return data

    probe_streams = probe_data.get_probe()["streams"]

    # Set file probe to shared infor for subsequent file test runners
    if 'shared_info' not in data:
        data['shared_info'] = {}
    data['shared_info']['ffprobe'] = probe_data.get_probe()

    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    search_language = settings.get_setting('search_language').strip().lower()
    
    if not search_language:
        logger.debug("No search language specified in settings.")
        return data

    matches = get_matching_streams(probe_streams, search_language)
    
    if len(matches) > 0:
        data['add_file_to_pending_tasks'] = True
        logger.debug(f"Found {len(matches)} streams matching '{search_language}'. Adding file to task list.")
    else:
        logger.debug(f"No streams matching '{search_language}' found.")

    return data

def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.
    """
    data['exec_command'] = []
    data['repeat'] = False

    abspath = data.get('file_in')
    outpath = data.get('file_out')

    probe_data = Probe(logger, allowed_mimetypes=['audio', 'video'])
    if probe_data.file(abspath):
        probe_streams = probe_data.get_probe()["streams"]
    else:
        logger.debug(f"Probe data failed - Nothing to encode - '{abspath}'")
        return data

    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    search_language = settings.get_setting('search_language').strip().lower()
    replace_language = settings.get_setting('replace_language').strip().lower()

    if not search_language or not replace_language:
        return data

    matches = get_matching_streams(probe_streams, search_language)
    
    if len(matches) > 0:
        ffmpeg_args = ['-hide_banner', '-loglevel', 'info', '-i', str(abspath), '-map', '0', '-c', 'copy']
        
        # Add metadata replacement for every matched stream
        for idx in matches:
            ffmpeg_args += [f'-metadata:s:{idx}', f'language={replace_language}']
            
        ffmpeg_args += ['-y', str(outpath)]
        
        data['exec_command'] = ['ffmpeg'] + ffmpeg_args

        # Set the parser for progress output
        try:
            parser = Parser(logger)
            parser.set_probe(probe_data)
            data['command_progress_parser'] = parser.parse_progress
        except Exception as e:
            logger.error(f"Could not configure parser: {e}")

    return data
