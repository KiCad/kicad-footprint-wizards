#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

from __future__ import division

#import sys
#sys.path.append("C:\\msys64\\mingw32\\lib\\python2.7\\site-packages")
#sys.path.append("C:\\msys64\\mingw32\\share\\kicad\\scripting\\plugins")
import pcbnew
import PadArray as PA
import FootprintWizardBase

class TestWizard(FootprintWizardBase.FootprintWizard):

    def GetName(self):
        return "TestFootprint"

    def GetDescription(self):
        return "Quad Flat Package footprint wizardess"

    def CheckParameters(self):
        self.CheckParam("Pads","n",min_value=100,info="This is a test error")
        
    def GenerateParameterList(self):
        print("Generating parameters")
        self.AddParam("Pads", "n", pcbnew.uInteger, 44, multiple=4, designator='A')
        self.AddParam("Pads", "pitch", pcbnew.uMM, 0.5, designator='Q')
        self.AddParam("Pads", "width", pcbnew.uMM, 0.25)
        self.AddParam("Pads", "length", pcbnew.uMM, 1.5)
        self.AddParam("Pads", "pitch", pcbnew.uMM, 15)
        self.AddParam("Pads", "pitch", "mm", 15)
        self.AddParam("Pads", "oval", pcbnew.uBool, True)

        self.AddParam("Package", "width", pcbnew.uMM, 14)
        self.AddParam("Package", "height", pcbnew.uMM, 14)
        self.AddParam("Package", "courtyard margin", pcbnew.uMM, 1)
        
        
        self.AddParam("guff","blob","percent","-23")
        
        self.AddParam("Options", "a",[1,2,3,4,5], 2)
        self.AddParam("Options", "B",[1,2,3,4,5], 3)
        self.AddParam("Options", "c","a,b,c,d,e","7a")
        self.AddParam("Options", "d","a,b,c,d,e","d")

    def GetValue(self):
        return "QFP_{d}".format(d=self.values['Pads']['n'])
        #return "QFP_%d" % self.parameters["Pads"]["n"]

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]

        pad_pitch = pads["pitch"]
        pad_length = pads["length"]
        pad_width = pads["width"]

        v_pitch = pads["pitch"]
        h_pitch = pads["pitch"]

        pads_per_row = pads["n"] // 4

        row_len = (pads_per_row - 1) * pad_pitch

        pad_shape = pcbnew.PAD_SHAPE_OVAL if pads["oval"] else pcbnew.PAD_SHAPE_RECT

        h_pad = PA.PadMaker(self.module).SMDPad( pad_length, pad_width,
                                                 shape=pad_shape, rot_degree=90.0)
        v_pad = PA.PadMaker(self.module).SMDPad( pad_length, pad_width, shape=pad_shape)

        #left row
        pin1Pos = pcbnew.wxPoint(-h_pitch / 2, 0)
        array = PA.PadLineArray(h_pad, pads_per_row, pad_pitch, True, pin1Pos)
        array.SetFirstPadInArray(1)
        array.AddPadsToModule(self.draw)

        #bottom row
        pin1Pos = pcbnew.wxPoint(0, v_pitch / 2)
        array = PA.PadLineArray(v_pad, pads_per_row, pad_pitch, False, pin1Pos)
        array.SetFirstPadInArray(pads_per_row + 1)
        array.AddPadsToModule(self.draw)

        #right row
        pin1Pos = pcbnew.wxPoint(h_pitch / 2, 0)
        array = PA.PadLineArray(h_pad, pads_per_row, -pad_pitch, True,
                                pin1Pos)
        array.SetFirstPadInArray(2*pads_per_row + 1)
        array.AddPadsToModule(self.draw)

        #top row
        pin1Pos = pcbnew.wxPoint(0, -v_pitch / 2)
        array = PA.PadLineArray(v_pad, pads_per_row, -pad_pitch, False,
                                pin1Pos)
        array.SetFirstPadInArray(3*pads_per_row + 1)
        array.AddPadsToModule(self.draw)

        lim_x = self.parameters["Package"]["width"] / 2
        lim_y = self.parameters["Package"]["height"] / 2
        inner = (row_len / 2) + pad_pitch

        #top left - diagonal
        self.draw.Line(-lim_x, -inner, -inner, -lim_y)
        # top right
        self.draw.Polyline([(inner, -lim_y), (lim_x, -lim_y), (lim_x, -inner)])
        # bottom left
        self.draw.Polyline([(-inner, lim_y), (-lim_x, lim_y), (-lim_x, inner)])
        # bottom right
        self.draw.Polyline([(inner, lim_y), (lim_x, lim_y), (lim_x, inner)])

        # Courtyard
        cmargin = self.parameters["Package"]["courtyard margin"]
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = (lim_x + cmargin) * 2 + pad_length
        sizey = (lim_y + cmargin) * 2 + pad_length
        # round size to nearest 0.1mm, rectangle will thus land on a 0.05mm grid
        sizex = pcbnew.PutOnGridMM(sizex, 0.1)
        sizey = pcbnew.PutOnGridMM(sizey, 0.1)
        # set courtyard line thickness to the one defined in KLC
        thick = self.draw.GetLineThickness()
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        # restore line thickness to previous value
        self.draw.SetLineThickness(pcbnew.FromMM(thick))

        #reference and value
        text_size = self.GetTextSize()  # IPC nominal
        text_offset = v_pitch / 2 + text_size + pad_length / 2

        self.draw.Value(0, text_offset, text_size)
        self.draw.Reference(0, -text_offset, text_size)

        # set SMD attribute
        self.module.SetAttributes(pcbnew.MOD_CMS)

TestWizard().register()

if __name__ == '__main__':
    w = TestWizard()

    w.BuildFootprint()
    print w.Show()
    print w.buildmessages