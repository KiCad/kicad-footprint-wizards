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

import FootprintWizardBase
import pcbnew
from pcbnew import *

class MutualcapButtonWizard(FootprintWizardBase.FootprintWizard):

    def GetName(self):
        """
        Return footprint name.
        This is specific to each footprint class, you need to implement this
        """
        return "Mutualcap Touch Button"

    def GetDescription(self):
        """
        Return footprint description.
        This is specific to each footprint class, you need to implement this
        """
        return "Wizard for Mutual Capacitance Touch Buttons."

    def GetValue(self):
        return "TouchButton-{width:g}x{height:g}mm".format(
            width = pcbnew.ToMM(self.pads["Width"]),
            height= pcbnew.ToMM(self.pads["Height"])
            )

    def GenerateParameterList(self):
        #self.AddParam("Pads", "panel_thickness",self.uMM)
        self.AddParam("Pads", "T (Panel thickness)", self.uMM, 1.6)
        self.AddParam("Pads", "Width", self.uMM, 12)
        self.AddParam("Pads", "Height", self.uMM, 12)
        self.AddParam("Pads", "Y width", self.uMM, 0.1)


    @property
    def pads(self):
        return self.parameters["Pads"]


    # build a rectangular pad
    def smdRectPad(self,module,size,pos,name):
        pad = D_PAD(module)
        pad.SetSize(size)
        pad.SetShape(PAD_SHAPE_RECT)
        pad.SetAttribute(PAD_ATTRIB_SMD)

        layerset = pcbnew.LSET()
        layerset.AddLayer(currentLayer)
        pad.SetLayerSet(layerset)

        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetName(name)
        return pad

    # This method checks the parameters provided to wizard and set errors
    def CheckParameters(self):
        pass

    def BuildThisFootprint(self):
        t  = self.pads["T (Panel thickness)"]
        w  = self.pads["Width"]
        h  = self.pads["Height"]
        yw = self.pads["Y width"]

        xFingers     = int((w-3*t-yw)/(1.5*t+yw))
        xBorderWidth = (w-t-yw-xFingers*(1.5*t+yw))/2
        clearance    = t/2

        ###border h
        self.module.SetLayer(F_Cu)
        size_pad = pcbnew.wxSize( w, t )
        self.module.Add(self.smdRectPad(self.module,size_pad, pcbnew.wxPoint(0,(-h/2)+t/2),str(1)))
        self.module.Add(self.smdRectPad(self.module,size_pad, pcbnew.wxPoint(0,( h/2)-t/2),str(1)))
        ###border v
        size_pad = pcbnew.wxSize(xBorderWidth, h-2*t)
        self.module.Add(self.smdRectPad(self.module,size_pad, pcbnew.wxPoint((-w/2)+xBorderWidth/2,0),str(1)))
        self.module.Add(self.smdRectPad(self.module,size_pad, pcbnew.wxPoint(( w/2)-xBorderWidth/2,0),str(1)))

        xPos = -w/2+xBorderWidth+clearance+yw
        xFingerSize = pcbnew.wxSize(t/2, h-t-yw-2*clearance-t)
        yFingerSize = pcbnew.wxSize(yw,h-2*t-2*clearance)
        #horizontal y-trace
        self.module.Add(self.smdRectPad(self.module,pcbnew.wxSize(w-2*xBorderWidth-2*clearance,yw), pcbnew.wxPoint(0,h/2-t-clearance-yw/2),str(2)))
        for i in range(0,xFingers):
            #y-fingers
            self.module.Add(self.smdRectPad(self.module,yFingerSize, pcbnew.wxPoint(xPos-yw/2 ,0),str(2)))
            #x-fingers
            self.module.Add(self.smdRectPad(self.module,xFingerSize, pcbnew.wxPoint(xPos+t*0.75,-w/h-t-yw/2+t/2),str(1)))
            xPos += t*1.5+yw

        #rightmost y-finger
        self.module.Add(self.smdRectPad(self.module,yFingerSize, pcbnew.wxPoint(xPos-yw/2,0),str(2)))

        textSize = self.GetTextSize()
        self.draw.Value(0, h/2+textSize, textSize)
        self.draw.Reference(0, -h/2-textSize, textSize)
        
        

MutualcapButtonWizard().register()