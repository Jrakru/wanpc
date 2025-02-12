# Advanced Configuration

Learn about advanced configuration options in wanpc.

## Defaults

Most commands have an interactive mode, however, if you would like to be more tech-savvy, you can manually enter all fields aswell
```bash
wanpc config set-default --name python-pkg --key author --value "Your Name"

wanpc config set-default --name python-pkg --key description --value "A basic description"

wanpc config set-global-default --key license --value MIT

wanpc config remove-default --name python-pkg --key author
```