<!-- Source: https://raw.githubusercontent.com/rclone/rclone/master/docs/content/docs.md
     Fetched: 2026-10-28. Excerpts: 'Configuration encryption' (from line 3202) and the RCLONE_PASSWORD_COMMAND part, verbatim. -->

## Configuration encryption

Your configuration file contains information for logging in to
your cloud services. This means that you should keep your
`rclone.conf` file in a secure location.

If you are in an environment where that isn't possible, you can
add a password to your configuration. This means that you will
have to supply the password every time you start rclone.

To add a password to your rclone configuration, execute `rclone config`.

```console
$ rclone config
```

Then source the file when you want to use it.  From the shell you
would do `source set-rclone-password`.  It will then ask you for the
password and set it in the environment variable.

An alternate means of supplying the password is to provide a script
which will retrieve the password and print on standard output.  This
script should have a fully specified path name and not rely on any
environment variables.  The script is supplied either via
[`--password-command="..."`](#password-command) command line argument or via the
`RCLONE_PASSWORD_COMMAND` environment variable.

One useful example of this is using the `passwordstore` application
to retrieve the password:

```console
export RCLONE_PASSWORD_COMMAND="pass rclone/config"
```

If the `passwordstore` password manager holds the password for the
rclone configuration, using the script method means the password
is primarily protected by the `passwordstore` system, and is never
embedded in the clear in scripts, nor available for examination
using the standard commands available.  It is quite possible with
long running rclone sessions for copies of passwords to be innocently
