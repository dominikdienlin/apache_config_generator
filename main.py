import os
from jinja2 import Template
import yaml
from subprocess import getoutput

apache_config_dir = "/etc/apache2/sites-enabled/"
config_path = "./config.yaml"

default_config = dict(
    defaults=dict(
        local_http_port=80,
        host="<hostname>",
        https_redirect=True
    )
)

template = Template("""\
<Virtualhost *:{{ local_http_port }}>
    ServerName {{ subdomain }}.{{ host }}
    ProxyPass / http://{{ ip }}:{{ port }}/
    ProxyPassReverse / http://{{ ip }}:{{ port }}/

    <Location "/ws">
       ProxyPass "ws://{{ ip }}:{{ port }}/ws"
    </Location>
{%- if https_redirect %}
    RewriteEngine on
    RewriteCond %{SERVER_NAME} ={{ subdomain }}.{{ host }}
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
{%- endif %}    

</Virtualhost>
""")


def check_apache_modules():
    required_mods = """proxy_module
    proxy_html_module
    proxy_http_module
    proxy_wstunnel_module
    rewrite_module
    ssl_module"""
    installed_mods = getoutput("apache2ctl -M")
    for mod in required_mods.split():
        if mod not in installed_mods:
            print("WARNING: mod %s doesn't seem to be activated")


def render_template(name, variables):
    for entry in "local_http_port ip port host".split():
        assert entry in variables
    return template.render(subdomain=name, **variables)


def render_templates(config):
    defaults = config["defaults"]
    for name, variables in config.items():
        if name == "defaults":
            continue

        vars_local = defaults.copy()
        vars_local.update(variables)

        result = render_template(name, vars_local)
        path = apache_config_dir+"/"+name+".conf"
        if os.path.isfile(path):
            if input("File %s already exists, would you like to overwrite it? (y/[n])" % path).lower().strip() != "y":
                continue
        with open(path, "w") as f:
            f.write(result)


if __name__ == "__main__":
    if not os.path.isdir(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    if not os.path.isfile(config_path):
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        print("generated default config at %s" % config_path)
    else:
        check_apache_modules()
        with open(config_path, "r") as f:
            config = yaml.load(f)
            render_templates(config)
