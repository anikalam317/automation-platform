"""
Plugin registry for dynamic discovery and management of laboratory automation plugins.

This module provides automatic discovery and registration of task, service, and instrument
plugins, enabling scalable addition of new functionality without modifying core code.
"""

import os
import importlib
import inspect
from typing import Dict, Type, List, Optional
from pathlib import Path
import logging

from .base import BasePlugin, TaskPlugin, ServicePlugin, InstrumentPlugin, PluginType

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing and discovering laboratory automation plugins."""
    
    def __init__(self):
        self._task_plugins: Dict[str, Type[TaskPlugin]] = {}
        self._service_plugins: Dict[str, Type[ServicePlugin]] = {}
        self._instrument_plugins: Dict[str, Type[InstrumentPlugin]] = {}
        self._plugin_instances: Dict[str, BasePlugin] = {}
    
    def register_task_plugin(self, name: str, plugin_class: Type[TaskPlugin]):
        """Register a task plugin class."""
        self._task_plugins[name] = plugin_class
        logger.info(f"Registered task plugin: {name}")
    
    def register_service_plugin(self, name: str, plugin_class: Type[ServicePlugin]):
        """Register a service plugin class."""
        self._service_plugins[name] = plugin_class
        logger.info(f"Registered service plugin: {name}")
    
    def register_instrument_plugin(self, name: str, plugin_class: Type[InstrumentPlugin]):
        """Register an instrument plugin class."""
        self._instrument_plugins[name] = plugin_class
        logger.info(f"Registered instrument plugin: {name}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin instance by name.
        
        Args:
            name: Plugin name to retrieve
            
        Returns:
            BasePlugin: Plugin instance or None if not found
        """
        if name in self._plugin_instances:
            return self._plugin_instances[name]
        
        # Try to create instance from registered classes
        plugin_class = None
        if name in self._task_plugins:
            plugin_class = self._task_plugins[name]
        elif name in self._service_plugins:
            plugin_class = self._service_plugins[name]
        elif name in self._instrument_plugins:
            plugin_class = self._instrument_plugins[name]
        
        if plugin_class:
            try:
                # Create instance and cache it
                instance = plugin_class()
                self._plugin_instances[name] = instance
                return instance
            except Exception as e:
                logger.error(f"Failed to create instance of plugin {name}: {e}")
                return None
        
        logger.warning(f"Plugin {name} not found in registry")
        return None
    
    def get_plugin_type(self, name: str) -> Optional[PluginType]:
        """Get the type of a plugin by name."""
        if name in self._task_plugins:
            return PluginType.TASK
        elif name in self._service_plugins:
            return PluginType.SERVICE
        elif name in self._instrument_plugins:
            return PluginType.INSTRUMENT
        return None
    
    def list_plugins(self) -> Dict[str, List[str]]:
        """
        List all registered plugins by type.
        
        Returns:
            Dict mapping plugin types to lists of plugin names
        """
        return {
            "tasks": list(self._task_plugins.keys()),
            "services": list(self._service_plugins.keys()),
            "instruments": list(self._instrument_plugins.keys())
        }
    
    def discover_plugins(self, plugin_dirs: List[str]):
        """
        Automatically discover and register plugins from specified directories.
        
        Args:
            plugin_dirs: List of directory paths to search for plugins
        """
        for plugin_dir in plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            self._discover_plugins_in_directory(plugin_dir)
    
    def _discover_plugins_in_directory(self, plugin_dir: str):
        """Discover plugins in a specific directory."""
        plugin_path = Path(plugin_dir)
        
        # Look for Python files in the directory
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py and __pycache__ files
            
            module_name = py_file.stem
            try:
                # Import the module using importlib
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin classes in the module
                    self._register_plugins_from_module(module)
                    
            except Exception as e:
                logger.error(f"Failed to load plugin module {py_file}: {e}")
    
    def _register_plugins_from_module(self, module):
        """Register plugins found in a module."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip the base classes themselves
            if obj in [BasePlugin, TaskPlugin, ServicePlugin, InstrumentPlugin]:
                continue
            
            # Check if it's a plugin class
            if issubclass(obj, TaskPlugin) and obj != TaskPlugin:
                # Create instance to get the plugin name
                try:
                    instance = obj()
                    self.register_task_plugin(instance.name, obj)
                except Exception as e:
                    logger.error(f"Failed to register task plugin {name}: {e}")
            
            elif issubclass(obj, ServicePlugin) and obj != ServicePlugin:
                try:
                    instance = obj()
                    self.register_service_plugin(instance.name, obj)
                except Exception as e:
                    logger.error(f"Failed to register service plugin {name}: {e}")
            
            elif issubclass(obj, InstrumentPlugin) and obj != InstrumentPlugin:
                try:
                    instance = obj()
                    self.register_instrument_plugin(instance.name, obj)
                except Exception as e:
                    logger.error(f"Failed to register instrument plugin {name}: {e}")


# Global plugin registry instance
plugin_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    return plugin_registry


def register_plugin(plugin_class: Type[BasePlugin]):
    """
    Decorator for registering plugins.
    
    Usage:
        @register_plugin
        class MyTaskPlugin(TaskPlugin):
            pass
    """
    try:
        instance = plugin_class()
        registry = get_plugin_registry()
        
        if isinstance(instance, TaskPlugin):
            registry.register_task_plugin(instance.name, plugin_class)
        elif isinstance(instance, ServicePlugin):
            registry.register_service_plugin(instance.name, plugin_class)
        elif isinstance(instance, InstrumentPlugin):
            registry.register_instrument_plugin(instance.name, plugin_class)
        else:
            logger.error(f"Unknown plugin type for {plugin_class.__name__}")
    
    except Exception as e:
        logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
    
    return plugin_class