from __future__ import unicode_literals

import click
from flask.cli import AppGroup, pass_script_info, with_appcontext

# XXX: Do not import any other snms modules here!
# If any import from this module triggers an exception the dev server
# will die while an exception only happening during app creation will
# be handled gracefully.
from snms.cli.util import SnmsFlaskGroup, LazyGroup


click.disable_unicode_literals_warning = True
__all__ = ('cli_command', 'cli_group')


# We never use the group but expose cli_command and cli_group for
# plugins to have access to the flask-enhanced command and group
# decorators that use the app context by default
_cli = AppGroup()
cli_command = _cli.command
cli_group = _cli.group
del _cli


@click.group(cls=SnmsFlaskGroup)
def cli():
    """
    This script lets you control various aspects of SNMS from the
    command line.
    """


# All core cli commands (including groups with subcommands) are
# registered in this file and imported lazily - either using a
# LazyGroup or by importing the actual logic of a command inside
# the command's function here.  This allows running the cli even
# if there's no snms config available or importing snms is
# broken for other reasons.

@cli.group(cls=LazyGroup, import_name='snms.cli.setup:cli')
def setup():
    """Setup SNMS."""

@cli.group(cls=LazyGroup, import_name='snms.cli.mqauth:cli')
def mqauth():
    """RabbitMQ Plugins."""


@cli.group(cls=LazyGroup, import_name='snms.cli.user:cli')
def user():
    """Manage SNMS users."""


@cli.group(cls=LazyGroup, import_name='snms.cli.database:cli')
def db():
    """Perform database operations."""


@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True}, add_help_option=False)
@click.pass_context
def celery(ctx):
    """Manage the Celery task daemon."""
    from snms.core.celery.cli import celery_cmd
    celery_cmd(ctx.args)


@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True}, add_help_option=False)
@click.pass_context
def mqtt(ctx):
    """Manage the Celery task daemon."""
    from snms.core.mqtt.cli import mqtt_cmd
    mqtt_cmd(ctx.args)


@cli.command(with_appcontext=False)
@click.option('--host', '-h', default='127.0.0.1', metavar='HOST', help='The ip/host to bind to.')
@click.option('--port', '-p', default=None, type=int, metavar='PORT', help='The port to bind to.')
@click.option('--url', '-u', default=None, metavar='URL',
              help='The URL used to access snms. Defaults to `http(s)://host:port`')
@click.option('--ssl', '-s', is_flag=True, help='Use SSL.')
@click.option('--ssl-key', '-K', type=click.Path(exists=True, dir_okay=False), help='The SSL private key to use.')
@click.option('--ssl-cert', '-C', type=click.Path(exists=True, dir_okay=False), help='The SSL cert key to use.')
@click.option('--quiet', '-q', is_flag=True, help='Disable logging of requests for most static files.')
@click.option('--enable-evalex', is_flag=True,
              help="Enable the werkzeug debugger's python shell in tracebacks and via /console")
@click.option('--evalex-from', multiple=True,
              help='Restrict the debugger shell to the given ips (can be used multiple times)')
@click.option('--proxy', is_flag=True, help='Use the ip and protocol provided by the proxy.')
@pass_script_info
def run(info, **kwargs):
    """Run the development webserver.

    If no port is set, 8000 or 8443 will be used (depending on whether
    SSL is enabled or not).

    Enabling SSL without specifying key and certificate will use a
    self-signed one.

    Specifying a custom URL allows you to run the dev server e.g. behind
    nginx to access it on the standard ports and serve static files
    much faster. Note that you MUST use `--proxy` when running behind
    another server; otherwise all requests will be considered to
    originate from that server's IP which is especially dangerous
    when using the evalex whitelist with `127.0.0.1` in it.

    Note that even behind nginx the dev server is NOT SUITABLE for a
    production setup.
    """
    from snms.cli.devserver import run_cmd
    if bool(kwargs['ssl_key']) != bool(kwargs['ssl_cert']):
        raise click.BadParameter('ssl-key and ssl-cert must be used together')
    run_cmd(info, **kwargs)


@cli.command(short_help='Run a shell in the app context.')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on the available objects')
@click.option('-r', '--request-context', is_flag=True, help='Run the shell inside a Flask request context')
def shell(verbose, request_context):
    from .shell import shell_cmd
    shell_cmd(verbose, request_context)
