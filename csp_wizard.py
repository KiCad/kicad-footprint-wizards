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
import pcbnew

import FootprintWizardBase
import PadArray as PA


class CSPPadGridArray(PA.PadGridArray):

    def __init__(self, pad, nx, ny, px, py, ox, mpad, centre=pcbnew.wxPoint(0, 0)):
        
        # this pad is more of a "context", we will use it as a source of
        # pad data, but not actually add it
        
        super(CSPPadGridArray, self).__init__(pad, nx, ny, px, py, centre)

        self.ox = ox
        self.mpad = mpad

        self.centre = centre

    def NamingFunction(self, n_x, n_y):
        if (self.ox != 0):
            return "%s%d" % (
                self.AlphaNameFromNumber(n_y + 1, alphabet="ABCDEFGHJKLMNPRTUVWY"),
                (2*(n_x +1) - (1*(n_y +1) % 2)  ))
                # 1 3 5 7 9 11
                #  2 4 6 8 10 12
        else:
            return "%s%d" % (
                self.AlphaNameFromNumber(n_y + 1, alphabet="ABCDEFGHJKLMNPRTUVWY"),
                n_x + 1 )

    #relocate the pad and add it as many times as we need
    def AddPadsToModule(self, dc):

        if (self.ox != 0) or (self.oy != 0): 
            nx = self.nx//2
        else:
            nx=self.nx

        pin1posX = self.centre.x - (self.px * (nx - 1) + self.ox ) / 2
        pin1posY = self.centre.y - (self.py * (self.ny - 1)) / 2


        for x in range(0, nx):
            for y in range(0, self.ny):
                if ((y % 2) != 0):
                    posX = pin1posX + (x * self.px) + self.ox 
                    posY = pin1posY + (y * (self.py))
                else:
                    posX = pin1posX + (x * self.px) 
                    posY = pin1posY + (y * (self.py))

                pos = dc.TransformPoint(posX, posY)
                pad = self.GetPad(x == 0 and y == 0, pos)
                Name = self.GetName(x,y)
                if Name not in self.mpad.split(','):
                    pad.SetName(Name)
                    self.AddPad(pad)



class CSPWizard(FootprintWizardBase.FootprintWizard):

    def GetName(self):
        return "CSP"

    def GetDescription(self):
        return "Chip Scale Package Footprint Wizard"

    def GenerateParameterList(self):
        self.AddParam("Pads", "pitchX", self.uMM, 0.6928, designator='p')
        self.AddParam("Pads", "pitchY", self.uMM, 0.2, designator='p')
        self.AddParam("Pads", "size", self.uMM, 0.015)
        self.AddParam("Pads", "columns", self.uInteger, 12, designator="nx")
        self.AddParam("Pads", "rows", self.uInteger, 17, designator="ny")
        self.AddParam("Pads", "rowoffsetx", self.uMM, 0.346400, designator="ox")
        self.AddParam("Pads", "missing pads", self.uString, "", designator="mpads")

        self.AddParam("Package", "width", self.uMM, 4.555, designator='X')
        self.AddParam("Package", "length", self.uMM, 3.646, designator='Y')
        self.AddParam("Package", "margin", self.uMM, 0.25, min_value=0.2, hint="Courtyard margin")

    def CheckParameters(self):

        # check that the package is large enough
        width = pcbnew.ToMM(self.parameters['Pads']['pitchX'] * self.parameters['Pads']['columns'])

        length = pcbnew.ToMM(self.parameters['Pads']['pitchY'] * self.parameters['Pads']['rows'])

        #self.CheckParam('Package','width',min_value=width,info="Package width is too small (< {w}mm)".format(w=width))
        #self.CheckParam('Package','length',min_value=length,info="Package length is too small (< {l}mm".format(l=length))

    def GetValue(self):
        pins = (self.parameters["Pads"]["rows"] * self.parameters["Pads"]["columns"]) 
        if self.parameters["Pads"]["rowoffsetx"] != 0:
            pins = pins//2 
        pins -= len(self.parameters["Pads"]["missing pads"].split(','))

        return "CSP-{n}_{x}x{y}mm_Layout{cols}x{rows}_P{px}x{py}-missing[{missing}]".format(
                n = pins,
                x = pcbnew.ToMM(self.parameters['Package']['width']),
                y = pcbnew.ToMM(self.parameters['Package']['length']),
                cols = self.parameters['Pads']['columns'],
                rows = self.parameters['Pads']['rows'],
                px = pcbnew.ToMM(self.parameters['Pads']['pitchX']),
                py = pcbnew.ToMM(self.parameters['Pads']['pitchY']),
                missing = self.parameters['Pads']['missing pads'])


    def BuildThisFootprint(self):

        pads = self.parameters["Pads"]

        rows = pads["rows"]
        cols = pads["columns"]
        pad_size = pads["size"]
        pad_size = pcbnew.wxSize(pad_size, pad_size)
        pad_pitchX = pads["pitchX"]
        pad_pitchY = pads["pitchY"]
        pad_rowoffsetx = pads["rowoffsetx"]
        pad_missing = pads["missing pads"]

        # add in the pads
        pad = PA.PadMaker(self.module).SMTRoundPad(pads["size"])

        pin1_pos = pcbnew.wxPoint(-((cols - 1) * pad_pitchX) / 2,
                                  -((rows - 1) * pad_pitchY) / 2)

        array = CSPPadGridArray(pad, cols, rows, pad_pitchX, pad_pitchY, pad_rowoffsetx,pad_missing)
        array.AddPadsToModule(self.draw)

        # Draw box outline on F.Fab layer
        self.draw.SetLayer(pcbnew.F_Fab)
        ssx = self.parameters['Package']['width'] / 2
        ssy = self.parameters['Package']['length'] / 2

        # Bevel should be 1mm nominal but we'll allow smaller values
        if pcbnew.ToMM(ssx) < 1:
            bevel = ssx
        else:
            bevel = pcbnew.FromMM(1)

        # Box with 1mm bevel as per IPC7351C
        self.draw.BoxWithDiagonalAtCorner(0, 0, ssx*2, ssy*2, bevel)

        # Add IPC markings to F_Silk layer
        self.draw.SetLayer(pcbnew.F_SilkS)
        offset = pcbnew.FromMM(0.15)
        len_x  = 0.5 * ssx
        len_y  = 0.5 * ssy

        edge = [
            [ ssx + offset - len_x, -ssy - offset],
            [ ssx + offset, -ssy - offset],
            [ ssx + offset, -ssy - offset + len_y],
               ]

        # Draw three square edges
        self.draw.Polyline(edge)
        self.draw.Polyline(edge, mirrorY=0)
        self.draw.Polyline(edge, mirrorX=0, mirrorY=0)

        # Draw pin-1 marker
        bevel += offset
        pin1 = [
            [ -ssx - offset + len_x, -ssy - offset],
            [ -ssx - offset + bevel, -ssy - offset],
            [ -ssx - offset, -ssy - offset + bevel],
            [ -ssx - offset, -ssy - offset + len_y],
                ]

        # Remove lines if the package is too small
        if bevel > len_x:
            pin1 = pin1[1:]

        if bevel > len_y:
            pin1 = pin1[:-1]

        self.draw.Polyline(pin1)

        # Draw a circle in the bevel void
        self.draw.Circle( -ssx, -ssy, pcbnew.FromMM(0.2), filled=True)

        # Courtyard
        cmargin = self.parameters['Package']['margin']
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = (ssx + cmargin) * 2
        sizey = (ssy + cmargin) * 2

        # round size to nearest 0.1mm, rectangle will thus land on a 0.05mm grid
        sizex = pcbnew.PutOnGridMM(sizex, 0.1)
        sizey = pcbnew.PutOnGridMM(sizey, 0.1)

        # set courtyard line thickness to the one defined in KLC
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        # restore line thickness to previous value
        self.draw.SetLineThickness(pcbnew.FromMM(cmargin))

        #reference and value
        text_size = self.GetTextSize()  # IPC nominal
        ypos = ssy + text_size
        self.draw.Value(0, ypos, text_size)
        self.draw.Reference(0, -ypos, text_size)

        # set SMD attribute
        self.module.SetAttributes(pcbnew.MOD_CMS)

CSPWizard().register()
