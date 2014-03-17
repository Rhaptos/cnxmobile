Installation
------------

1. Bootstrap and run buildout:

    $ virtualenv --no-site-packages .
    $ ./bin/python bootstrap.py
    $ ./bin/buildout

2. Configure ports in etc/deliverance.xml

3. Customise font paths in
   src/upfront.mathmlimage/upfront/mathmlimage/svgmath.xml

   If you want to use the true type fonts referenced in the config
   file you simply install the ttf-freefont and msttcorefonts package on
   debian or ubuntu.

4. Start deliverance-proxy:

    $ ./bin/deliverance-proxy ./etc/deliverance.xml

5. Browse to http://localhost:8080

