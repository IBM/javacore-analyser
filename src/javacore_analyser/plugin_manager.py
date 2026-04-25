#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Plugin manager for javacore-analyser.

This module provides the :class:`PluginManager` class which handles discovery,
loading, and management of data source plugins. The plugin manager scans a
designated plugin directory, dynamically loads plugin modules, and provides
access to registered plugins for file processing.

The plugin system allows users to extend javacore-analyser with custom data
source handlers without modifying the core codebase. Plugins are discovered
from the user's home directory at ``~/.javacore_analyser/plugins/``.

Each plugin must:

- Reside in its own subdirectory under the plugins directory
- Contain a ``plugin.py`` file with at least one :class:`DataSourcePlugin` subclass
- Implement all required abstract methods from the plugin interface

The plugin manager provides robust error handling to ensure that a single
failing plugin does not prevent other plugins from loading or break the
application.
"""

from __future__ import annotations

import fnmatch
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from javacore_analyser.plugin_interface import DataSourcePlugin
from javacore_analyser.properties import Properties

class PluginManager:
    """
    Manages plugin discovery, loading, and access.

    The plugin manager is responsible for:

    - Locating the user plugin directory
    - Scanning for plugin modules
    - Dynamically loading plugin classes
    - Providing access to loaded plugins
    - Mapping files to appropriate plugins based on file patterns

    Plugins are loaded from ``~/.javacore_analyser/plugins/`` where each plugin
    resides in its own subdirectory containing a ``plugin.py`` file.

    Example directory structure::

        ~/.javacore_analyser/plugins/
        ├── threaddump/
        │   └── plugin.py
        └── customlog/
            └── plugin.py

    The plugin manager automatically discovers and instantiates all
    :class:`DataSourcePlugin` subclasses found in plugin modules.
    """

    def __init__(self) -> None:
        """
        Initialize the plugin manager.

        Sets up internal storage for loaded plugins and determines the plugin
        directory location. The plugin directory is created if it does not exist.
        """
        self._plugins: Dict[str, DataSourcePlugin] = {}
        self._plugin_directory: Path = self._get_plugin_directory()
        logging.info(f"Plugin manager initialized with directory: {self._plugin_directory}")

    def _get_plugin_directory(self) -> Path:
        """
        Get plugin directory from configuration or use default.
        Creates directory if it doesn't exist.

        The plugin directory can be configured via the ``plugin_directory``
        property in config.ini. If not configured, defaults to
        ``~/.javacore_analyser/plugins/``.

        Returns:
            Path object representing the plugin directory.
        """
        # Check if custom plugin directory is configured
        custom_dir = Properties.get_instance().get_property("plugin_directory", None)

        if custom_dir:
            plugin_dir = Path(custom_dir).expanduser()
            logging.info(f"Using configured plugin directory: {plugin_dir}")
        else:
            plugin_dir = Path.home() / ".javacore_analyser" / "plugins"
            logging.debug(f"Using default plugin directory: {plugin_dir}")

        plugin_dir.mkdir(parents=True, exist_ok=True)
        return plugin_dir

    def discover_plugins(self) -> None:
        """
        Discover and load all plugins from the plugin directory.

        Scans the plugin directory for subdirectories containing ``plugin.py``
        files. Each valid plugin module is loaded, and all :class:`DataSourcePlugin`
        subclasses are instantiated and registered.

        Failed plugin loads are logged but do not prevent other plugins from
        loading. This ensures that a single broken plugin does not break the
        entire plugin system.

        The method logs:

        - Info messages for successfully loaded plugins
        - Warning messages for plugins that fail to load
        - Debug messages for directory scanning operations
        """
        if not self._plugin_directory.exists():
            logging.warning(f"Plugin directory does not exist: {self._plugin_directory}")
            return

        logging.info(f"Discovering plugins in: {self._plugin_directory}")

        for item in self._plugin_directory.iterdir():
            if item.is_dir():
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    logging.debug(f"Found plugin file: {plugin_file}")
                    self._load_plugin(item)
                else:
                    logging.debug(f"Skipping directory without plugin.py: {item}")

        logging.info(f"Plugin discovery complete. Loaded {len(self._plugins)} plugin(s)")

    def _load_plugin(self, plugin_dir: Path) -> None:
        """
        Load a single plugin from the specified directory.

        Dynamically imports the ``plugin.py`` module from the plugin directory,
        searches for :class:`DataSourcePlugin` subclasses, instantiates them,
        and registers them by their plugin name.

        Args:
            plugin_dir: Path to the plugin directory containing ``plugin.py``.

        The method handles the following error conditions:

        - Module import failures
        - Missing or invalid plugin classes
        - Plugin instantiation errors
        - Duplicate plugin names

        All errors are logged as warnings, and the plugin load is aborted without
        affecting other plugins.
        """
        plugin_name = plugin_dir.name
        plugin_file = plugin_dir / "plugin.py"
        module_name = f"javacore_analyser_plugin_{plugin_name}"

        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                logging.warning(f"Failed to load plugin spec from: {plugin_file}")
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find all DataSourcePlugin subclasses in the module
            plugin_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, DataSourcePlugin) and
                        attr is not DataSourcePlugin):
                    plugin_classes.append(attr)

            if not plugin_classes:
                logging.warning(f"No DataSourcePlugin subclasses found in: {plugin_file}")
                return

            # Instantiate and register each plugin class
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    plugin_id = plugin_instance.get_plugin_name()

                    if plugin_id in self._plugins:
                        logging.warning(
                            f"Duplicate plugin name '{plugin_id}' from {plugin_file}. "
                            f"Skipping duplicate."
                        )
                        continue

                    self._plugins[plugin_id] = plugin_instance
                    logging.info(
                        f"Loaded plugin: {plugin_instance.get_display_name()} "
                        f"(id: {plugin_id}) from {plugin_dir.name}"
                    )

                except Exception as e:
                    logging.warning(
                        f"Failed to instantiate plugin class {plugin_class.__name__} "
                        f"from {plugin_file}: {e}"
                    )

        except Exception as e:
            logging.warning(f"Failed to load plugin from {plugin_file}: {e}")

    def get_plugin(self, name: str) -> Optional[DataSourcePlugin]:
        """
        Get a plugin by its unique name.

        Args:
            name: The unique plugin identifier returned by
                :meth:`DataSourcePlugin.get_plugin_name`.

        Returns:
            The plugin instance if found, otherwise ``None``.
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[DataSourcePlugin]:
        """
        Get all loaded plugins.

        Returns:
            A list of all successfully loaded plugin instances.
        """
        return list(self._plugins.values())

    def find_files_for_plugins(self, directory: str) -> Dict[DataSourcePlugin, List[str]]:
        """
        Scan a directory and map files to plugins that can process them.

        For each loaded plugin, this method:

        1. Gets the plugin's file patterns via :meth:`DataSourcePlugin.get_file_patterns`
        2. Scans the directory for files matching those patterns
        3. Validates each candidate file with :meth:`DataSourcePlugin.can_process`
        4. Maps successfully validated files to their corresponding plugin

        Args:
            directory: Path to the directory to scan for plugin-compatible files.

        Returns:
            A dictionary mapping plugin instances to lists of file paths they can
            process. Plugins with no matching files are not included in the result.

        Example::

            plugin_files = manager.find_files_for_plugins("/path/to/data")
            for plugin, files in plugin_files.items():
                print(f"{plugin.get_display_name()}: {len(files)} file(s)")
                data = plugin.process_files(files)
        """
        result: Dict[DataSourcePlugin, List[str]] = {}
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            logging.warning(f"Directory does not exist or is not a directory: {directory}")
            return result

        for plugin in self._plugins.values():
            matching_files: List[str] = []

            try:
                patterns = plugin.get_file_patterns()
                logging.debug(
                    f"Scanning for {plugin.get_display_name()} with patterns: {patterns}"
                )

                # Scan directory for files matching plugin patterns
                for file_path in dir_path.rglob("*"):
                    if not file_path.is_file():
                        continue

                    # Check if filename matches any of the plugin's patterns
                    filename = file_path.name
                    for pattern in patterns:
                        if fnmatch.fnmatch(filename, pattern):
                            # Validate with plugin's can_process method
                            try:
                                if plugin.can_process(str(file_path)):
                                    matching_files.append(str(file_path))
                                    logging.debug(
                                        f"File {file_path} matched plugin "
                                        f"{plugin.get_plugin_name()}"
                                    )
                            except Exception as e:
                                logging.warning(
                                    f"Error validating file {file_path} with plugin "
                                    f"{plugin.get_plugin_name()}: {e}"
                                )
                            break  # Don't check other patterns for this file

                if matching_files:
                    result[plugin] = matching_files
                    logging.info(
                        f"Found {len(matching_files)} file(s) for plugin "
                        f"{plugin.get_display_name()}"
                    )

            except Exception as e:
                logging.warning(
                    f"Error scanning files for plugin {plugin.get_plugin_name()}: {e}"
                )

        return result


# Made with Bob