# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2021 Koninklijke Philips N.V. All Rights Reserved.
# A copyright license is hereby granted for redistribution and use of the
# Software in source and binary forms, with or without modification, provided
# that the following conditions are met:
# • Redistributions of source code must retain the above copyright notice, this
#   copyright license and the following disclaimer.
# • Redistributions in binary form must reproduce the above copyright notice,
#   this copyright license and the following disclaimer in the documentation
#   and/ or other materials provided with the distribution.
# • Neither the name of Koninklijke Philips N.V. nor the names of its
#   subsidiaries may be used to endorse or promote products derived from the
#   Software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Backend Selection file
"""
from __future__ import absolute_import
import sys


# pylint: disable = too-few-public-methods
class Backend:
    """
    Class to get backend
    """

    def __init__(self, name, context, backend):
        """
        Constructor
        """
        self.name = name
        self.context = context[0]
        self.backend = backend[0]
        self.context_class = context[1]
        self.backend_class = backend[1]


class Backends:
    """
    Backends class
    """
    def __init__(self):
        """
        Constructor
        """
        # iterate over backend libraries that might or might not be available
        self.backends = [
            Backend('SOFTWARE', ['softwarerendercontext', 'SoftwareRenderContext'],
                    ['softwarerenderbackend', 'SoftwareRenderBackend']),
            Backend('GLES2', ['eglrendercontext', 'EglRenderContext'],
                    ['gles2renderbackend', 'Gles2RenderBackend']),
            Backend('GLES3', ['eglrendercontext', 'EglRenderContext'],
                    ['gles3renderbackend', 'Gles3RenderBackend'])
        ]

        valid_backends = []
        for backend in self.backends:
            try:
                if backend.context not in sys.modules:
                    context_lib = __import__(backend.context)
                if backend.backend not in sys.modules:
                    backend_lib = __import__(backend.backend)
            except ImportError:
                pass
            else:
                backend.context = getattr(context_lib, backend.context_class)
                backend.backend = getattr(backend_lib, backend.backend_class)
                valid_backends.append(backend)

        self.backends = valid_backends

    def initialize_backend(self, backend):
        """
        Method to initialize backend
        """
        render_backend = [x.backend for x in self.backends if x.name == backend][0]()
        render_context = [x.context for x in self.backends if x.name == backend][0]()
        return render_backend, render_context
