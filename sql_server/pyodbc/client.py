import re
import subprocess

from django.db.backends.base.client import BaseDatabaseClient

class DatabaseClient(BaseDatabaseClient):
    executable_name = 'sqlcmd'

    def runshell(self):
        settings_dict = self.connection.settings_dict
        options = settings_dict['OPTIONS']

        user = options.get('user', settings_dict['USER'])
        server = options.get('host', settings_dict['HOST'])
        password = options.get('passwd', settings_dict['PASSWORD'])
        db = options.get('db', settings_dict['NAME'])

        driver = options.get('driver', 'ODBC Driver 13 for SQL Server')
        ms_drivers = re.compile('^ODBC Driver .* for SQL Server$|^SQL Server Native Client')

        if not ms_drivers.match(driver):
            self.executable_name = options.get('client', 'isql')

        if self.executable_name == 'sqlcmd':
            port = options.get('port', settings_dict['PORT'])
            defaults_file = options.get('read_default_file')

            args = [self.executable_name]
            if server:
                if port:
                    server = ','.join((server, str(port)))
                args += ["-S", server]
            if user:
                args += ["-U", user]
                if password:
                    args += ["-P", password]
            else:
                args += ["-E"] # Try trusted connection instead
            if db:
                args += ["-d", db]
            if defaults_file:
                args += ["-i", defaults_file]

        elif self.executable_name == 'tsql':
            opts = 'opts' in options and ['-o', options['opts']] or []
            tdelim = 'tdelm' in options and ["-t", options['tdelm']] or []
            rdelim = 'rdelm' in options and ["-r", options['rdelm']] or []
            args = [
                self.executable_name, '-S', server, '-U', user, '-P', password, '-D', db, 
            ] + opts + tdelim + rdelim

        else:
            dsn = options.get('dsn', '')
            args = [self.executable_name, '-v', dsn, user, password]

        try:
            subprocess.check_call(args)
        except KeyboardInterrupt:
            pass
