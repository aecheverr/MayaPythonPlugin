#Alt + Shift + M == Send code to Maya
#commandPort -n "localhost:7001" -stp "mel";
import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mel
from maya.OpenMaya import MVector
from PySide2.QtWidgets import QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

class LimbRiggerWidget(QWidget):
    def __init__(self):
        mayaMainWindow = LimbRiggerWidget.GetMayaMainWindow()

        for existing in mayaMainWindow.findChildren(QWidget, LimbRiggerWidget.GetWindowUniqueId()):
            existing.deleteLater()

        super().__init__(parent=mayaMainWindow)
        self.setWindowTitle("Limb Rigger")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(LimbRiggerWidget.GetWindowUniqueId())

        self.controllerSize = 10
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Please Select the Root, Middle, and End Joint of the Limb(In Order):"))

        ctrlSizeLayout = QHBoxLayout()
        self.masterLayout.addLayout(ctrlSizeLayout)

        ctrlSizeLayout.addWidget(QLabel("Controller Size: "))
        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setValue(self.controllerSize)
        ctrlSizeSlider.setMinimum(1)
        ctrlSizeSlider.setMaximum(30)
        ctrlSizeLayout.addWidget(ctrlSizeSlider)

        self.ctrlSizeLabel = QLabel(str(self.controllerSize))
        ctrlSizeLayout.addWidget(self.ctrlSizeLabel)
        ctrlSizeSlider.valueChanged.connect(self.ControllerSizeUpdated)

        buildLimbRigbtn = QPushButton("Build")
        buildLimbRigbtn.clicked.connect(self.BuildRig)
        self.masterLayout.addWidget(buildLimbRigbtn)

    def BuildRig(self):
        selection = mc.ls(sl=True)

        rootJnt = selection[0]
        midJnt = selection[1]
        endJnt = selection[2]

        rootCtrl, rootCtrlGrp = self.CreatorFKCtrlForJnt(rootJnt)
        midCtrl, midCtrlGrp = self.CreatorFKCtrlForJnt(midJnt)
        endCtrl, endCtrlGrp = self.CreatorFKCtrlForJnt(endJnt)

        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(midCtrlGrp, rootCtrl)

        ikEndCtrlName, ikEndCtrlGrpName, poleVectorCtrlName, poleVectorCtrlGrpName, ikHandleName = self.BuildIkControls(rootJnt, midJnt, endJnt)

        ikfkBlendCtrlName = "ac_ikfk_blend_" + rootJnt
        ikfkBlendCtrlGrpName = ikfkBlendCtrlName ="_grp"

        mel.eval(f"curve -d 1 -n {ikfkBlendCtrlName} -p -1 2 0 -p 1 2 0 -p 1 0 0 -p 3 0 0 -p 3 -2 0 -p 1 -2 0 -p 1 -4 0 -p -1 -4 0 -p -1 -2 0 -p -3 -2 0 -p -3 0 0 -p -1 0 0 -p -1 2 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        mc.group(ikfkBlendCtrlName, n = ikfkBlendCtrlGrpName)

        rootJntPos = mc.xform(rootJnt, q=True, ws=True, t=True)
        mc.move(rootJntPos[0] * 2, rootJntPos[1], rootJntPos[2], ikfkBlendCtrlGrpName)

        ikfkBlendAttr = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrlName, ln=ikfkBlendAttr, k = True, min = 0, max = 1)
        
        endJoinOrientConstraint = mc.listConnections(endJnt, s=True, type = "orientConstraint")[0]

        mc.expression(s=f"{rootCtrlGrp}.v=1 - {ikfkBlendCtrlName}.{ikfkBlendAttr}")
        mc.expression(s=f"{ikEndCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttr}")
        mc.expression(s=f"{poleVectorCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttr}")
        mc.expression(s=f"{ikHandleName}.ikBlend={ikfkBlendCtrlName}.{ikfkBlendAttr}")
        mc.expression(s=f"{endJoinOrientConstraint}.{endCtrl}W0=1-{ikfkBlendCtrlName}.{ikfkBlendAttr}")
        mc.expression(s=f"{endJoinOrientConstraint}.{ikEndCtrlName}W1={ikfkBlendCtrlName}.{ikfkBlendAttr}")

        topGrpName = rootJnt + "_rig_grp"
        mc.group([ikEndCtrlGrpName, poleVectorCtrlGrpName, rootCtrlGrp, ikfkBlendCtrlGrpName], n = topGrpName)

    def BuildIkControls(self, rootJnt, midJnt, endJnt):
        endCtrlName = "a_ik_" + endJnt
        endCtrlGrpName = endCtrlName + "_grp"
        mel.eval(f"curve -d 1 -n {endCtrlName} -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, endCtrlName, r=True)
        mc.makeIdentity(endCtrlName, apply = True) #freeze Transformation
        mc.group(endCtrlName, n = endCtrlGrpName)
        mc.matchTransform(endCtrlGrpName, endJnt)
        mc.orientConstraint(endCtrlName, endJnt)

        #ikHandle
        ikHandleName = "ikHandle_" + endJnt
        mc.ikHandle(n = ikHandleName, sj = rootJnt, ee = endJnt, sol = "ikRPsolver")

        #get(q=True) the world space(ws=True) translation(t=True) of the root joint, returns a list of 3 values [x,y,z]
        rootJntPosVals = mc.xform(rootJnt, q = True, ws = True, t = True)
        rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals[1], rootJntPosVals[2])

        endJntPosVals = mc.xform(endJnt, q = True, ws = True, t = True)
        endJntPos = MVector(endJntPosVals[0], endJntPosVals[1], endJntPosVals[2])

        poleVectorVals = mc.getAttr(ikHandleName+".poleVector")[0]
        poleVector = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])

        rootToEndVector = endJntPos - rootJntPos
        limbDirOffset = rootToEndVector/2

        poleVector.normalize()
        poleVectorOffset = poleVector * rootToEndVector.length()

        poleVectorCtrlPos = rootJntPos + limbDirOffset + poleVectorOffset

        poleVectorCtrlName = "ac_ik_" + midJnt
        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
        mc.spaceLocator(n=poleVectorCtrlName)
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)
        mc.move(poleVectorCtrlPos[0], poleVectorCtrlPos[1], poleVectorCtrlPos[2], poleVectorCtrlGrpName)

        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)
        mc.parent(ikHandleName, endCtrlName)

        return endCtrlName, endCtrlGrpName, poleVectorCtrlName, poleVectorCtrlGrpName, ikHandleName

    
    def CreatorFKCtrlForJnt(self, jnt):
        ctrlName = "ac_fk_" + jnt
        ctrlGrpName = ctrlName + "_grp"
        mc.circle(n=ctrlName, r=self.controllerSize, nr=(1,0,0))
        mc.group(ctrlName, n = ctrlGrpName)
        mc.matchTransform(ctrlGrpName, jnt)
        mc.orientConstraint(ctrlName, jnt)
        return ctrlName, ctrlGrpName

    def ControllerSizeUpdated(self, newSize):
        self.controllerSize = newSize
        self.ctrlSizeLabel.setText(str(newSize))

    @staticmethod
    def GetMayaMainWindow():
        mayaMainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mayaMainWindow), QMainWindow)

    @staticmethod
    def GetWindowUniqueId():
        return "adwuiaefgiwufgbi"

def Run():
    LimbRiggerWidget().show()