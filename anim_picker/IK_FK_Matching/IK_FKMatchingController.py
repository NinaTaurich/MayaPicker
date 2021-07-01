import maya.cmds as cmds
from maya import OpenMayaAnim
from maya import OpenMaya as om
import pymel.core as pm
from MayaPicker.anim_picker.IK_FK_Matching import matchingSetupWindow
from six.moves import reload_module
reload_module(matchingSetupWindow)

import logging
logging.basicConfig()
logger = logging.getLogger("matching")
logger.setLevel(logging.DEBUG)

debug = False
debugZero = False

class MatchingController:
    def __init__(self, ifOnInit, parent):
        global win
        win ='ikfkswitchUI_'

        self.ifOn = ifOnInit
        self.limb = {}
        self.switchAttr = ""
        self.arm= []
        self.fakes = []
        self.parent = parent

    def on_keyframe_set(keyframes, client_data):
        print("keyframe set")
        cmds.setKeyframe("RocketGirl_Rig_v1_6:LeftForeArm_FK_CTRL")

    def openSetupWindow(self):
        self.matchingWindow = matchingSetupWindow.matchingSetupWindowUI(self)

    def updateMode(self):
        """
        run when object selected. Switches between ik and fk and matches when one of the ik/fk controls is selected
        :return:
        """
        currSelection = cmds.ls(selection = True) #current selection

        for key in self.limb.keys():
            #if mode is opposite
            switchCtrl = self.limb[key]['switchCtrl']
            switchAttr = self.limb[key]['switchAttr']
            switch = '%s.%s'%(switchCtrl, switchAttr)
            if(cmds.getAttr(switch)== 1.0):
                #in fk mode
                #check if selection contains an ik control
                if((self.limb[key]["ikpv"] in currSelection) or (self.limb[key]["ikwrist"] in currSelection)):
                    self.matchFkIkWin(key) #match fk to ik
                    logger.debug("switch to ik")
                    self.switchIkFK(0.0,key) #switch to ik
            else:
                #in ik mode
                #check if selection contains an fk control
                if((self.limb[key]["fkwrist"] in currSelection) or (self.limb[key]["fkellbow"] in currSelection) or (self.limb[key]["fkshldr"] in currSelection)):
                    self.matchIkFkWin(key) #match ik to fk
                    logger.debug("print to fk")
                    self.switchIkFK(1.0,key) #switch to fk

    def turnOn(self):
        """
        sets up matching mode
        :return: None
        """
        logger.debug("turn on")
        self.ifOn = True
        self.matchingWindow.close() #close setup window

        # #create fakes
        # self.fakes.append(self.duplicateControl(self.arm[3]))
        # self.fakes.append(self.duplicateControl(self.arm[2]))
        # # fk_wristFake = cmds.duplicate(self.arm[2], parentOnly=1, n='fk_wristFake')[0]
        # # unlockAttributes([fk_wristFake])

        #start script job to check when ik/fk controls selected
        self.sj = cmds.scriptJob(event= ["SelectionChanged", lambda: self.updateMode()], parent ="PickerUI")

        #callback for keyframe
        # self.keyframe_callback = OpenMayaAnim.MAnimMessage.addAnimKeyframeEditedCallback(self.on_keyframe_set)
        logger.debug("make callback")

    def turnOff(self):
        """
        stops matching mode
        :return: None
        """
        logger.debug("turn off")
        self.ifOn= False
        self.parent.MatchingModeBtn.setChecked(False) #make matching button unchecked/not selected

        #kill script job
        logger.debug("kill ik fk script job")
        if hasattr(self,"sj"):
            cmds.scriptJob(kill=self.sj)

        #delete fakes
        # for control in self.fakes:
        #     cmds.delete(control)

        #close setup window if still open
        if(self.matchingWindow):
            self.matchingWindow.close()

        #remove keyframe callback
        # OpenMaya.MMessage.removeCallback(self.keyframe_callback)
        logger.debug("delete callback")

    def duplicateControl(self, object):
        """
        create a fake control from given control
        :param object: control to duplicate
        :return:
        """
        fake = object +"fake"
        cmds.duplicate(object, rr=True, n=fake)[0]
        unlockAttributes([fake])
        cmds.parent(fake,w=True, a=True)
        cmds.parentConstraint(object, fake, mo=True, weight = 1)
        return fake

    def switchIkFK(self, ikfkValue, key):
        if(self.ifOn):
            switchCtrl = self.limb[key]["switchCtrl"]
            switchAttr = "IK_FK"
            switch = '%s.%s'%(switchCtrl, switchAttr)
            cmds.setAttr(switch, ikfkValue)

            #switch around fakes
            # if(ikfkValue == 0.0): #change to ik
            #     #make fk disapear
            #     cmds.hide(self.fakes[0])
            #     cmds.showHidden(self.fakes[1])
            # if(ikfkValue == 1.0): #change to fk
            #     #make ik disapear
            #     cmds.hide(self.fakes[1])
            #     cmds.showHidden(self.fakes[0])


    def matchIkFkWin(self, key):
        """
        match ik to fk with entered info
        :param key: the limb being matched
        :return: None
        """
        fkshldr = self.limb[key]["fkshldr"]
        fkellbow= self.limb[key]["fkellbow"]
        fkwrist= self.limb[key]["fkwrist"]
        ikpv = self.limb[key]["ikpv"]
        ikwrist = self.limb[key]["ikwrist"]
        switchCtrl = self.limb[key]["switchCtrl"]
        switchAttr = self.limb[key]["switchAttr"]
        side, limb = key.split("_")
        switch0isfk = 0

        ikfkMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=switch0isfk, switchAttrRange=1, rotOffset=[0,0,0], side=side, limb=limb, guessUp=1, bendKneeAxis='+X')

    def matchFkIkWin(self, key):
        """
        match fk to ik with entered info
        :param key: the limb being matched
        :return: None
        """
        fkshldr = self.limb[key]["fkshldr"]
        fkellbow= self.limb[key]["fkellbow"]
        fkwrist= self.limb[key]["fkwrist"]
        ikpv = self.limb[key]["ikpv"]
        ikwrist = self.limb[key]["ikwrist"]
        switchCtrl = self.limb[key]["switchCtrl"]
        switchAttr = self.limb[key]["switchAttr"]
        side, limb = key.split("_")
        switch0isfk=0

        fkikMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=switch0isfk, switchAttrRange=1, rotOffset=[0,0,0], side=side, limb=limb)


"""
The code below are copyright of Monika Gelbmann 2021 and released under the MIT license
"""
def ikfkMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=1, switchAttrRange=1, rotOffset=[0,0,0], side='R', limb='arm', guessUp=1, bendKneeAxis='+X'):
    '''
    Snap fk to ik controls by building ik joint form fk control position and lining up to ik
    Args:
    Returns:

    '''
    print(fkwrist)
    ns = fkwrist.split(':')[0]
    switch = '%s.%s'%(switchCtrl, switchAttr)
    clist = []

    if pm.objExists('snapGrp'): pm.delete('snapGrp')
    snapGrp = pm.createNode('transform', name='snapGrp')

    # store if keyframe on ik attribute or not:
    ikwrist_key = pm.keyframe(ikwrist, q=1, t=pm.currentTime())
    ikpv_key = pm.keyframe(ikpv, q=1, t=pm.currentTime())

    logger.info( 'matching. switch attr range is %s'%switchAttrRange           )
    # go to fk mode to match correct position (some riggs use same foot ctrl for ik and fk)
    if switch0isfk == 0:      pm.setAttr(switch, switchAttrRange)  # 0 is fk
    else:   pm.setAttr(switch, 0)

    # zero out fk
    pm.xform(fkshldr, ro=(0,0,0))
    pm.xform(fkellbow, ro=(0,0,0))
    pm.xform(fkwrist, ro=(0,0,0))

    try : pm.xform(fkshldr, t=(0,0,0))
    except:pass
    try : pm.xform(fkellbow, t=(0,0,0))
    except:pass
    try : pm.xform(fkwrist, t=(0,0,0))
    except:pass

    logger.info('root loc')
    pm.dgdirty([fkshldr, fkellbow, fkwrist])
    root_loc = pm.group(empty=1, n='fk_shld_root')
    pm.parent(root_loc, snapGrp)
    snap(fkshldr, root_loc)

    fkshldr_dup = pm.duplicate(fkshldr, parentOnly=1)[0]
    fkellbow_dup = pm.duplicate(fkellbow, parentOnly=1)[0]
    fkwrist_dup = pm.duplicate(fkwrist, parentOnly=1)[0]

    #unlock all of duplicate A's arrtibutes
    basicTransforms = ['translateX','translateY','translateZ', 'translate', 'rotateX','  rotateY','rotateZ', 'rotate']
    for attr in basicTransforms:
        #unlock attr
        pm.setAttr((fkshldr_dup + '.' + attr), lock=False, k=True)
        pm.setAttr((fkellbow_dup + '.' + attr), lock=False, k=True)
        pm.setAttr((fkwrist_dup + '.' + attr), lock=False, k=True)
        pm.select([fkshldr_dup, fkellbow_dup, fkwrist_dup])
        logger.info('line up fk duplicates to fk controlssss %s %s %s'%(fkshldr_dup, fkellbow_dup, fkwrist_dup))

    # line up fk duplicates to fk controls
    pm.parent(fkshldr_dup, snapGrp)
    snap(fkshldr, fkshldr_dup, pos=1, rot=1)
    pm.parent(fkellbow_dup,fkshldr_dup)
    snap(fkellbow, fkellbow_dup, pos=1, rot=1)
    pm.parent(fkwrist_dup, fkellbow_dup)
    snap(fkwrist, fkwrist_dup, pos=1, rot=1)
    pm.select(snapGrp)
    logger.info('snapping fk shoulder to ik')

    root_ikSnap = pm.joint(n='root_ikSnap', p=pm.xform(fkshldr, t=1, q=1, ws=1), orientation=(0, 0, 0))
    pm.parent(root_ikSnap, root_loc)
    snap(fkshldr, root_ikSnap, rot=1, pos=1)
    ikshldr_jnt = pm.joint(n='ikshldr_jnt', p=pm.xform(fkshldr, t=1, q=1, ws=1), orientation=(0, 0, 0))
    snap(fkellbow, ikshldr_jnt, rot=1, pos=0)
    try: snap(fkshldr, ikshldr_jnt, rot=0, pos=1)
    except: pass
    logger.info('snapping fk ellbow to ik')
    ikellbow_jnt = pm.joint(n='ikellbow_jnt', p=pm.xform(fkellbow, t=1, q=1, ws=1), orientation=(0, 0, 0))
    snap(fkellbow, ikellbow_jnt, rot=1, pos=0)
    try: snap(fkellbow, ikellbow_jnt, rot=0, pos=1)
    except: pass
    logger.info('snapping fk wrist to ik')
    ikwrist_jnt = pm.joint(n='ikwrist_jnt', p=pm.xform(fkwrist, t=1, q=1, ws=1), orientation=(0, 0, 0))
    snap(fkellbow, ikwrist_jnt, rot=1, pos=0)
    try: snap(fkwrist, ikwrist_jnt, rot=0, pos=1)
    except: pass
    #aimaxis = max(pm.getAttr('%s.tx'%ikellbow_jnt), pm.getAttr('%s.tx'%ikellbow_jnt), pm.getAttr('%s.tx'%ikellbow_jnt))
    logger.info('freeze transform')
    pm.makeIdentity(ikshldr_jnt, apply=1)
    pm.makeIdentity(ikellbow_jnt, apply=1)
    pm.makeIdentity(ikwrist_jnt, apply=1)

    multiplyer = 1
    if bendKneeAxis[0] == '-':
        mutliplyer = -1
    if abs(pm.getAttr('%s.jointOrient%s'%(ikellbow_jnt, bendKneeAxis[1]))) < 0.1:
        pm.warning('Warning small joint orient. Setting Prefferec Angle to Y '  )
        pm.setAttr('%s.preferredAngle%s'%(ikellbow_jnt, bendKneeAxis[1]), 12.0*multiplyer)
        pm.setAttr('%s.jointOrient%s'%(ikellbow_jnt, bendKneeAxis[1]), 0.01*multiplyer)

    # pole vector
    pole_ikSnap = pm.spaceLocator(n='pole_ikSnap')
    pm.parent(pole_ikSnap, fkellbow_dup)

    logger.info('snap pole ik to fkellbow knee bend axis is %s'%bendKneeAxis)
    # temp pole vector position. use the ellbow could use poleVectorPos as well
    snap(fkellbow_dup, pole_ikSnap)

    logger.info('considering kneebendaxis. %s'%bendKneeAxis)
    reverse = 1
    if side == 'L': reverse = -1

    if bendKneeAxis == '-X':
        pole_ikSnap.tz.set(pole_ikSnap.tz.get()+0.5*reverse)
    elif bendKneeAxis == '+X':
        pole_ikSnap.tz.set(pole_ikSnap.tz.get()-0.5*reverse)
    elif bendKneeAxis == '-Y':
        pole_ikSnap.tz.set(pole_ikSnap.tz.get()+0.5*reverse)
    elif bendKneeAxis == '+Y':
        pole_ikSnap.tz.set(pole_ikSnap.tx.get()-0.5*reverse)
    elif bendKneeAxis == '-Z':
        pole_ikSnap.ty.set(pole_ikSnap.ty.get()-0.5*reverse)
    elif bendKneeAxis == '+Z':
        pole_ikSnap.ty.set(pole_ikSnap.ty.get()+0.5*reverse)

    pm.parent(pole_ikSnap, snapGrp)

    # ik handle
    ikHandle_ikSnap = pm.ikHandle(sj=ikshldr_jnt, ee=ikwrist_jnt, sol='ikRPsolver')
    pm.parent(ikHandle_ikSnap[0], snapGrp)

    pm.poleVectorConstraint(pole_ikSnap, ikHandle_ikSnap[0])
    logger.info( 'done polevector constraint' )

    # wrist offset locator line up to zero out ikwrist
    ikrot = pm.xform(ikwrist, q=1,  ro=1)
    pm.xform(ikwrist, ro=(0,0,0))
    ikwrist_loc = pm.spaceLocator(n='ikwrist_loc')
    pm.setAttr('%s.rotateOrder'%ikwrist_loc, pm.getAttr('%s.rotateOrder'%ikwrist))
    pm.parent(ikwrist_loc, fkwrist_dup)
    snap(fkwrist, ikwrist_loc, rot=0, pos=1)
    snap(fkwrist, ikwrist_loc, rot=1, pos=0)

    ikwrist_loc_offset = pm.spaceLocator(n='ikwrist_loc_offset')
    pm.setAttr('%s.rotateOrder'%ikwrist_loc_offset, pm.getAttr('%s.rotateOrder'%ikwrist))
    pm.parent(ikwrist_loc_offset, ikwrist_loc)
    snap(ikwrist_jnt, ikwrist_loc_offset, rot=0, pos=1)
    snap(fkwrist, ikwrist_loc_offset, rot=1, pos=0)

    # considering rotation offset (reverse)
    logger.info( 'considering rotation offset' )
    fkwrist_rotOrder = pm.getAttr('%s.rotateOrder'%fkwrist)
    ikwrist_rotOrder = pm.getAttr('%s.rotateOrder'%ikwrist)
    logger.debug('rotation order ikwrist: %s. fkwrist: %s'%(fkwrist_rotOrder,ikwrist_rotOrder))
    pm.setAttr('%s.rx'%ikwrist_loc_offset, rotOffset[0] )
    pm.setAttr('%s.ry'%ikwrist_loc_offset, rotOffset[1] )
    pm.setAttr('%s.rz'%ikwrist_loc_offset, rotOffset[2] )


    # constrain fk ctrl dups to ikSnap locs
    logger.info( 'constrain fk ctrl dups to ikSnap locs' )
    clist.append(pm.parentConstraint(ikshldr_jnt, fkshldr_dup,  skipTranslate = ['x', 'y', 'z'], mo=1)   )
    clist.append(pm.parentConstraint(ikellbow_jnt, fkellbow_dup, skipTranslate = ['x', 'y', 'z'], mo=1)      )
    clist.append(pm.parentConstraint(ikwrist_jnt, fkwrist_dup, mo=1)      )

    fkwrist_loc = pm.spaceLocator(n='fkwrist_loc')
    pm.setAttr('%s.rotateOrder'%fkwrist_loc, pm.getAttr('%s.rotateOrder'%fkwrist))
    pm.parent(fkwrist_loc, ikwrist_loc_offset)
    snap(fkwrist, fkwrist_loc)
    pm.setAttr('%s.rx'%ikwrist_loc_offset,0)
    pm.setAttr('%s.ry'%ikwrist_loc_offset, 0)
    pm.setAttr('%s.rz'%ikwrist_loc_offset, 0)

    # rotate back ik
    logger.info( 'rotate back ik' )
    pm.xform(ikwrist, ro=ikrot)
    clist.append(pm.parentConstraint(ikwrist, ikwrist_loc, mo=0)    )

    if debugZero:
        return

    # switch to ik mode (some riggs use same foot ctrl for ik and fk)
    if switch0isfk == 0:      pm.setAttr(switch, 0)  # 0 is fk
    else:   pm.setAttr(switch, switchAttrRange)

    # line up to ik wrist and pole
    logger.info( 'line up to ik wrist and pole' )
    clist.append(pm.pointConstraint(ikwrist, ikHandle_ikSnap[0]))
    snap(ikpv, pole_ikSnap, rot=0, pos=1)

    # get wrist rotation
    #snap(ikwrist, fkwrist_loc, rot=1, pos=0)
    # snap(fkshldr_loc, fkshldr, rot=1, pos=0)
    # snap(fkellbow_loc, fkellbow, rot=1, pos=0)
    # snap(fkwrist_loc, fkwrist,  rot=1, pos=0)
    logger.debug('snapping back to original fk')
    # snap back to original fk ctlrs
    for ctrl in [fkshldr, fkellbow, fkwrist]:
        if len(pm.keyframe(ctrl, q=1))>0:
            pm.cutKey(ctrl, t=pm.currentTime())

    logger.info( 'snap fk shoulder' )
    snap(fkshldr_dup, fkshldr, rot=1, pos=0)
    try: snap(fkshldr_dup, fkshldr, pos=1)
    except: pass
    logger.info( 'snap fk ellbow' )
    snap(fkellbow_dup, fkellbow, rot=1, pos=0)
    try: snap(fkellbow_dup, fkellbow, pos=1)
    except: pass
    logger.info( 'snap fk wrist' )
    snap(fkwrist_loc, fkwrist, rot=1, pos=0)
    try: snap(fkwrist_loc, fkwrist, pos=1)
    except: pass

    for ctrl in [fkshldr, fkellbow, fkwrist]:
        if len(pm.keyframe(ctrl, q=1))>0:
            pm.setKeyframe(ctrl, t=pm.currentTime(), s=0)

    pm.dgdirty([fkshldr, fkellbow, fkwrist])

    # debug mode
    if debug == True:
        pm.parentConstraint(fkwrist_loc, fkwrist, mo=0, st=('x', 'y', 'z'))

    # clean up
    if debug == False:
        pm.delete(clist)
        pm.delete(snapGrp)

    # clean up eventually created keyframe on ik ctrl on switch frame
    if len(ikwrist_key) == 0:
        try : pm.cutKey(ikwrist, t=pm.currentTime())
        except: pass
    if len(ikpv_key) == 0:
        try : pm.cutKey(ikpv, t=pm.currentTime())
        except: pass

    # set to ik
    if switch0isfk == 0: pm.setAttr(switch, 1)
    else: pm.setAttr(switch, 0)

def fkikMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=1, switchAttrRange=1, rotOffset=[0,0,0], side='R', limb='arm'):
	'''
	Match fk to ik. Recreate the ik chain
	Args:
		fkwrist:
		fkellbow:
		fkshldr:
		ikwrist:
		ikpv:
		switchCtrl:
		switchAttr:
		switch0isfk:
		rotOffset:

	Returns:

	'''
	switch = '%s.%s'%(switchCtrl, switchAttr)

	if pm.objExists('snapGrp'): pm.delete('snapGrp')
	snapGrp = pm.createNode('transform', name='snapGrp')
	clist=[]


	# dup controls to constrain
	fk_wristDup = pm.duplicate(fkwrist, parentOnly=1, n='fk_wristDup')[0]
	unlockAttributes([fk_wristDup])
	pm.parent(fk_wristDup, snapGrp)


	# go to fk mode to match correct position
	if switch0isfk == 0:      pm.setAttr(switch, switchAttrRange)  # 0 is fk
	else:   pm.setAttr(switch, 0)


	# store fk keyframes on attribute or not:
	fkwrist_key, fkellbow_key, fkshldr_key = pm.keyframe(fkwrist, q=1, t=pm.currentTime()),\
											 pm.keyframe(fkellbow, q=1, t=pm.currentTime()),\
											 pm.keyframe(fkshldr, q=1, t=pm.currentTime())


	# get positions from fk
	fkwRaw = pm.xform(fkwrist, ws=1, q=1, t=1)
	fkwPos = om.MVector(fkwRaw[0], fkwRaw[1], fkwRaw[2])
	fkeRaw = pm.xform(fkellbow, ws=1, q=1, t=1)
	fkePos = om.MVector(fkeRaw[0], fkeRaw[1], fkeRaw[2])
	fksRaw = pm.xform(fkshldr, ws=1, q=1, t=1)
	fksPos = om.MVector(fksRaw[0], fksRaw[1], fksRaw[2])

	# store rotation
	fkwRotRaw = pm.xform(fkwrist,  q=1, ro=1)
	fkeRotRaw = pm.xform(fkellbow, q=1, ro=1)
	fksRotRaw = pm.xform(fkshldr,  q=1, ro=1)

	# zero out fk
	pm.xform(fkshldr, ro=(0,0,0))
	pm.xform(fkellbow, ro=(0,0,0))
	pm.xform(fkwrist, ro=(0,0,0))
	snap(fkwrist, fk_wristDup)

	# create orig ik wrist dup to get offset
	pm.xform(ikwrist, ro=(0,0,0))
	ik_wristDup = pm.duplicate(ikwrist, parentOnly=1,  n='ik_wristDup')[0]
	unlockAttributes([ik_wristDup])
	pm.parent(ik_wristDup, fk_wristDup)
	snap(fk_wristDup, ik_wristDup, pos=1, rot=1)
	#snap(ikwrist, ik_wristDup, pos=0, rot=1)

	ik_wristDupOffset = pm.duplicate(ik_wristDup, parentOnly=1,  n='ik_wristDup_offset')[0]
	pm.parent(ik_wristDupOffset, ik_wristDup)

	clist.append(pm.parentConstraint(fkwrist,fk_wristDup, mo=0))


	# restore fk
	pm.xform(fkshldr, ro=fksRotRaw)
	pm.xform(fkellbow, ro=fkeRotRaw)
	pm.xform(fkwrist, ro=fkwRotRaw)

	#considering rotation offset
	pm.setAttr('%s.rx'%ik_wristDupOffset, rotOffset[0])
	pm.setAttr('%s.ry'%ik_wristDupOffset, rotOffset[1])
	pm.setAttr('%s.rz'%ik_wristDupOffset, rotOffset[2])


	# pole vector
	fkshldr_dup = pm.spaceLocator(n='fkShld_dup')
	snap(fkshldr, fkshldr_dup)
	pm.parent(fkshldr_dup, snapGrp)
	fkellbow_dup = pm.spaceLocator(n='fkEllbow_dup')
	snap(fkellbow, fkellbow_dup)
	pm.parent(fkellbow_dup, snapGrp)
	fkwrist_dup = pm.spaceLocator(n='fkwrist_dup')
	snap(fkwrist, fkwrist_dup)
	pm.parent(fkwrist_dup, snapGrp)
	pvLoc = poleVectorPosition(fkshldr_dup, fkellbow_dup, fkwrist_dup, length=12, createLoc =1)
	pm.select([fkshldr, fkellbow, fkwrist])
	pm.parent(pvLoc, snapGrp)

	# snap ik
	for ctrl in [ikwrist, ikpv]:
		if len(pm.keyframe(ctrl, q=1))>0:
			pm.cutKey(ctrl, t=pm.currentTime())

	snap(ik_wristDupOffset, ikwrist)
	snap(pvLoc, ikpv, pos=1, rot=0)

	for ctrl in [ikwrist, ikpv]:
		if len(pm.keyframe(ctrl, q=1))>0:
			pm.setKeyframe(ctrl, t=pm.currentTime(), s=0)

	if debug == True:
		clist.append(pm.parentConstraint(ik_wristDupOffset, ikwrist))

	# clean up
	if debug == False:
		pm.delete(clist)
		pm.delete(snapGrp)

		#pm.delete(pvLoc)
		#if not debug: pm.delete(fkRotLocWs)

	# clean up eventually created keyframe on fk ctrl on switch frame
	if len(fkwrist_key) == 0:
		try : pm.cutKey(fkwrist, t=pm.currentTime())
		except: pass
	if len(fkellbow_key) == 0:
		try : pm.cutKey(fkellbow, t=pm.currentTime())
		except: pass
	if len(fkshldr_key) == 0:
		try : pm.cutKey(fkshldr, t=pm.currentTime())
		except: pass


	# go to ik mode
	if switch0isfk == 0:      pm.setAttr(switch, 0)
	else:   pm.setAttr(switch, switchAttrRange)

	pm.dgdirty([ikwrist, ikpv])
	pm.dgdirty([fkwrist, fkellbow, fkshldr])

	logger.info( 'Done matching FK to IK.')


# Align with Parent Constrain
def snap(master=None, slave=None, pos=1, rot=1):
    '''
    Snap slave to master. Check if attribute locked and skip
    '''
    lastSel = pm.selected()

    if master == None:
        master = pm.selected()[0]
    if slave == None:
        slave = pm.selected()[1:]
    slaves = pm.ls(slave)

    ptC, ptR = [], []

    # for each slave, parentconstrain for each position and rotation, skipping locked attributes
    for slave in slaves:

        slaveDup = pm.duplicate(slave, parentOnly=True)[0]
        logger.debug('snapping slaveDup')

        #unlock all of duplicate A's arrtibutes
        basicTransforms = ['translateX','translateY','translateZ', 'translate','rotateX','rotateY','rotateZ','rotate']
        for attr in basicTransforms:
            #unlock attr
            pm.setAttr((slaveDup + '.' + attr), lock=False, k=1)

        ptC=pm.parentConstraint(master, slaveDup, mo=False)

        if pos == 1:
            for att in ['tx', 'ty', 'tz']:
                if pm.getAttr('%s.%s'%(slave,att), l=1) == False:
                    pm.setAttr((slave + '.' + att), pm.getAttr((slaveDup + '.' + att)))

                    logger.info('Snap Constraining Traslation %s %s. Skiplist is '%(master, slave)  )


        if rot == 1:
            for att in ['rx', 'ry', 'rz']:
                if pm.getAttr('%s.%s'%(slave,att), l=1) == False:
                    pm.setAttr((slave + '.' + att), pm.getAttr((slaveDup + '.' + att)))

                    logger.info('Snap Constraining Rotation %s %s. Skiplist is '%(master, slave))

        pm.delete(ptC)
        pm.delete(slaveDup)

    pm.select(lastSel)

def poleVectorPosition(startJnt, midJnt, endJnt, length=12, createLoc =0):

	import maya.api.OpenMaya as om

	start = pm.xform(startJnt ,q= 1 ,ws = 1,t =1 )
	mid = pm.xform(midJnt ,q= 1 ,ws = 1,t =1 )
	end = pm.xform(endJnt ,q= 1 ,ws = 1,t =1 )
	startV = om.MVector(start[0] ,start[1],start[2])
	midV = om.MVector(mid[0] ,mid[1],mid[2])
	endV = om.MVector(end[0] ,end[1],end[2])


	startEnd = endV - startV
	startMid = midV - startV

	# projection vector is vecA projected onto vecB
	# it is calculated by dot product if one vector normalized

	# proj= vecA * vecB.normalized (dot product result is scalar)
	proj = startMid * startEnd.normal()


	# multiply proj scalar with normalized startEndVector to project it onto vector
	startEndN = startEnd.normal()
	projV = startEndN * proj

	arrowV = startMid - projV
	arrowVN = arrowV.normal()

	# scale up to length and offset to midV
	finalV = arrowVN*length + midV


	if createLoc:
		loc = pm.spaceLocator(n='polePos')
		pm.xform(loc , ws =1 , t= (finalV.x , finalV.y ,finalV.z))
		return loc

	return finalV


def unlockAttributes(objects, attributes=['translate','translateX','translateY','translateZ','rotateX','  rotateY','rotateZ', 'visibility']):
    #unlock all of duplicate A's arrtibutes
    for obj in objects:
        foundObjects = pm.ls(obj)
        obj = foundObjects[0]
        print(obj)
        for a in attributes:
            obj.attr(a).unlock()
            pm.setAttr((obj + '.' + a), lock=False, k=True)





