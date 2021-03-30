# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# Copyright 2003 Duke University

from __future__ import print_function, absolute_import
from __future__ import unicode_literals

import rpm
import os
import re

from dnf.i18n import ucd


def checkSig(ts, package):
    """Takes a transaction set and a package, check it's sigs,
    return 0 if they are all fine
    return 1 if the gpg key can't be found
    return 2 if the header is in someway damaged
    return 3 if the key is not trusted
    return 4 if the pkg is not gpg or pgp signed"""

    value = 4
    currentflags = ts.setVSFlags(0)
    fdno = os.open(package, os.O_RDONLY)
    try:
        hdr = ts.hdrFromFdno(fdno)
    except rpm.error as e:
        if str(e) == "public key not available":
            value = 1
        elif str(e) == "public key not trusted":
            value = 3
        elif str(e) == "error reading package header":
            value = 2
        else:
            raise ValueError('Unexpected error value %r from ts.hdrFromFdno when checking signature.' % str(e))
    else:
        # checks signature from an hdr
        string = '%|DSAHEADER?{%{DSAHEADER:pgpsig}}:{%|RSAHEADER?{%{RSAHEADER:pgpsig}}:' \
                 '{%|SIGGPG?{%{SIGGPG:pgpsig}}:{%|SIGPGP?{%{SIGPGP:pgpsig}}:{(none)}|}|}|}|'
        try:
            siginfo = hdr.sprintf(string)
            siginfo = ucd(siginfo)
            rpm_pgpsig_format_regex = re.compile(r'[0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}, Key ID [0-9a-f]{16}\Z')

            if siginfo == '(none)':
                value = 4
            elif rpm_pgpsig_format_regex.search(siginfo):
                value = 0
            else:
                raise ValueError('Unexpected return value %r from hdr.sprintf when checking signature.' % siginfo)
        except UnicodeDecodeError:
            pass

        del hdr

    os.close(fdno)

    ts.setVSFlags(currentflags)  # put things back like they were before
    return value
