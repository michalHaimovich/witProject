import click
import wit
import Exeptions
import os


@click.group()
def cli():
    pass


@cli.command()
def init():
    try:
        path = os.getcwd()
        wit.init(path)
    except Exeptions.WitError as e:
        click.secho('WitError'+str(e), fg='red')
    except OSError as e:
        click.echo(f"An error occurred: {e}")
    else:
        click.secho(f"Successfully initialized .wit in: {path}", fg='green')


@cli.command()
@click.argument('path')
def add(path):
    try:
        wit.add(path)
    except Exeptions.WitError as e:
        click.secho('WitError'+str(e), fg='red')
    except FileNotFoundError as e:
        click.secho(str(e), fg='red')
    except Exception as e:
        click.secho(f"Failed to add : {e}", fg='red')
    else:
        click.secho(f"Added files to staging area.", fg='green')


@cli.command()
@click.option('-m', '--message', required=True, help='Commit message')
def commit(message):
    try:
       new_id = wit.commit(message)
    except Exeptions.WitError as e:
        click.secho('WitError'+str(e), fg='red')
    except Exception as e:
        click.secho(f"Error creating commit: {e}", fg='red')
    else:
        click.secho(f"Commit created successfully! ID: {new_id}, Message: {message}", fg='green')


@cli.command()
@click.argument('commit_id')
def checkout(commit_id):
    try:
        wit.checkout(commit_id)
    except Exeptions.WitError as e:
        click.secho('WitError'+str(e), fg='red')
    except Exception as e:
        click.secho(f"Fatal error during checkout: {e}", fg='red')
    else:
        click.secho(f"HEAD is now at {commit_id}", fg='green')


@cli.command()
def status():
    try:
        commit_id, changes_to_be_committed, untracked_files, modified_not_staged = wit.status()
    except Exeptions.WitError as e:
        click.secho('WitError' + str(e), fg='red')
    else:
        click.secho(f"On commit: {commit_id if commit_id != 'None' else 'No commits yet'}\n", bold=True)
        # 1. Files staged but not included in the last commit
        click.secho("1. Files staged but not included in the last commit:", fg='yellow', bold=True)
        if changes_to_be_committed:
            for f in sorted(changes_to_be_committed):
                click.secho(f"\t{f}", fg='green')
        else:
            click.echo("\t(none)")
        click.echo("")  # שורה ריקה

        # 2. Untracked files
        click.secho("2. Untracked files:", fg='yellow', bold=True)
        if untracked_files:
            for f in sorted(untracked_files):
                click.secho(f"\t{f}", fg='red')
        else:
            click.echo("\t(none)")
        click.echo("")

        # 3. Files modified in the working directory but not staged
        click.secho("3. Files modified in the working directory but not staged:", fg='yellow', bold=True)
        if modified_not_staged:
            for f in sorted(modified_not_staged):
                click.secho(f"\t{f}", fg='red')
        else:
            click.echo("\t(none)")
        click.echo("")


if __name__ == '__main__':
    cli()
