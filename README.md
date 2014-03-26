cnxmobile
=========

Mobile site for OpenStax CNX using Deliverance

Installation
------------

1. Bootstrap and run buildout:

```sh
$ virtualenv --no-site-packages .
$ ./bin/python bootstrap.py
$ ./bin/buildout
```

2. Configure ports in etc/deliverance.xml and users in etc/deliv-users.htpasswd

3. Customise font paths in
   src/upfront.mathmlimage/upfront/mathmlimage/svgmath.xml

   If you want to use the true type fonts referenced in the config
   file, simply install the ttf-freefont and msttcorefonts packages on
   debian or ubuntu.

4. Start deliverance-proxy:

```sh
$ ./bin/deliverance-proxy ./etc/deliverance.xml
```

5. Browse to http://localhost:port
