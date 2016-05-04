#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import direct3d_vertexshader, direct3d_pixelshader, direct3d_allow_multisampling, direct3d_antialiasing, direct3d_offscreen_rendering, direct3d_video_memory_size, directx_capture_mouse, directinput_mouse_warp, graphics_xrandr, direct3d_csmt, direct3d_dxva2_vaapi
from vineyard.widgets import sound_driver, sound_directsound_acceleration, sound_directsound_samplerate, sound_directsound_bitdepth, sound_directsound_emulation

id = 'devices'
position = 0.3

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        page.VineyardPage.__init__(self,
            name = _("Devices"),
            icon = 'applications-multimedia',
            pages = [
                (_('Graphics'), [
                    (_('Direct3D'), [
                        direct3d_vertexshader,
                        direct3d_pixelshader,
                        direct3d_antialiasing,
                        direct3d_allow_multisampling,
                        directx_capture_mouse,
                        graphics_xrandr,
                        directinput_mouse_warp,
                        direct3d_offscreen_rendering
                    ]),
                    (_('Direct3D Video Memory size'), [
                        direct3d_video_memory_size
                    ]),
                    (_('Direct3D Staging Features'), [
                        direct3d_csmt,
                        direct3d_dxva2_vaapi
                    ])
                ]),
                (_('Sound'), [
                    (_('Sound Output'), [
                        sound_driver
                    ]),
                    (_('DirectSound Emulation'), [
                        sound_directsound_acceleration,
                        sound_directsound_samplerate,
                        sound_directsound_bitdepth,
                        sound_directsound_emulation
                    ])
                ])
            ])

