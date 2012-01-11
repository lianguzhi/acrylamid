#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see acrylamid.py

import sys
import os
import glob
import logging

import traceback

sys.path.insert(0, os.path.dirname(__file__))
log = logging.getLogger('acrylamid.views')

# module-wide callbacks variable contaning views
__views_list = []


def get_views():

    global __views_list
    return __views_list


def index_views(module, urlmap, conf, env):
    """Stupid an naïve try getting attribute specified in `views` in
    various flavours and fail silent.

    We remove already mapped urls and pop views'name from kwargs to
    avoid the practical worst-case O(m*n), m=num rules, n=num modules.

    Views are stored into module-global variable `callbacks` and can be
    retrieved using :func:`views.get_views`.
    """

    global __views_list

    for view, rule in urlmap[:]:
        try:
            mem = getattr(module, view)
        except AttributeError:
            try:
                mem = getattr(module, view.capitalize())
            except AttributeError:
                try:
                    mem = getattr(module, view.lower())
                except AttributeError:
                    try:
                        mem = getattr(module, view.upper())
                    except AttributeError:
                        mem = None
        if mem:
            kwargs = conf['views'][rule].copy()
            kwargs.pop('view')
            __views_list.append(mem(conf, env, path=rule, **kwargs))
            urlmap.remove((view, rule))


def initialize(ext_dir, conf, env):

    # view -> path
    urlmap = [(conf['views'][k]['view'], k) for k in conf['views']]

    # handle ext_dir
    for mem in ext_dir[:]:
        if os.path.isdir(mem):
            sys.path.insert(0, mem)
        else:
            ext_dir.remove(mem)
            log.error("Extension directory %r does not exist. -- skipping" % mem)

    ext_dir.extend([os.path.dirname(__file__)])
    ext_list = []

    for mem in ext_dir:
        files = glob.glob(os.path.join(mem, "*.py"))
        files += [p.rstrip('/__init__.py') for p in \
                    glob.glob(os.path.join(mem, '*/__init__.py'))]
        ext_list += files

    for mem in [os.path.basename(x).replace('.py', '') for x in ext_list]:
        if mem.startswith('_'):
            continue
        try:
            _module = __import__(mem)
            #sys.modules[__package__].__dict__[mem] = _module
            index_views(_module, urlmap, conf, env)
        except (ImportError, Exception), e:
            log.error('%r ImportError %r', mem, e)
            traceback.print_exc(file=sys.stdout)


class View(object):

    __view__ = True
    __filters__ = True
