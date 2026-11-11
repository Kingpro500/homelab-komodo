#!/bin/sh
# nginx 'user nobody;' krever gruppen nobody; Debian-imaget har bare nogroup.
grep -q '^nobody:' /etc/group || echo 'nobody:x:65534:' >> /etc/group
