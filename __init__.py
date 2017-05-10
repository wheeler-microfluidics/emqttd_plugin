import logging
import subprocess as sp

from microdrop.plugin_helpers import get_plugin_info
from microdrop.plugin_manager import (PluginGlobals, Plugin, IPlugin,
                                      implements)
import conda_helpers as ch
import path_helpers as ph

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

logger = logging.getLogger(__name__)

# Store location of `emqttd.cmd` script for convenient access.
EMQTTD_CMD = ch.conda_prefix().joinpath('Library', 'opt', 'emqttd', 'bin',
                                        'emqttd.cmd')


def is_emqttd_running():
    '''
    Returns
    -------
    bool
        ``True`` if `emqttd` service is running.
    '''
    return sp.check_output([EMQTTD_CMD, 'ping'], shell=True).strip() == 'pong'


def emqttd_exec(*args):
    '''
    Execute `emqttd.cmd` command with the provided arguments.

    Returns
    -------
    str
        Output from executed command.
    '''
    # Start `emqttd` service.
    return sp.check_output([EMQTTD_CMD] + list(args), shell=True)


def emqttd_start():
    '''
    Start `emqttd` service (if not already running).

    Returns
    -------
    bool
        ``True`` if service was started.

        ``False`` if service was already running.

    Raises
    ------
    RuntimeError
        If `emqttd` service does not respond to a ``ping`` command.
    '''
    if is_emqttd_running():
        return False

    # Start `emqttd` service.
    emqttd_exec('start')
    # Verify `emqttd` service is running.
    if not is_emqttd_running():
        raise RuntimeError('Error starting `emqttd` service.')

    return True


def emqttd_stop():
    '''
    Stop `emqttd` service (if running).

    Returns
    -------
    bool
        ``True`` if service was stopped

        ``False`` if service was not running.

    Raises
    ------
    RuntimeError
        If `emqttd` service still responds to a ``ping`` command.
    '''
    if not is_emqttd_running():
        return False

    # Stop `emqttd` service.
    emqttd_exec('stop')
    # Verify `emqttd` service is running.
    if is_emqttd_running():
        raise RuntimeError('Error stopping `emqttd` service.')

    return True


PluginGlobals.push_env('microdrop.managed')

class EmqttdPlugin(Plugin):
    """
    This class is automatically registered with the PluginManager.
    """
    implements(IPlugin)
    version = __version__
    plugin_name = get_plugin_info(ph.path(__file__).parent).plugin_name

    def __init__(self):
        self.name = self.plugin_name
        # Flag to indicate whether or not we started the `emqttd` service.
        # Used to determine if we should **stop** the service when the plugin
        # is disabled.
        self.launched_service = False

    def on_plugin_enable(self):
        """
        Handler called once the plugin instance is enabled.

        Note: if you inherit your plugin from AppDataController and don't
        implement this handler, by default, it will automatically load all
        app options from the config file. If you decide to overide the
        default handler, you should call:

            AppDataController.on_plugin_enable(self)

        to retain this functionality.
        """
        super(EmqttdPlugin, self).on_plugin_enable()

        # Launch `emqttd` service (if not already running).
        self.launched_service = emqttd_start()

    def on_plugin_disable(self):
        """
        Handler called once the plugin instance is disabled.
        """
        if self.launched_service:
            # We started the `emqttd` service, so stop it.
            emqttd_stop()


PluginGlobals.pop_env()
