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
    def __init__(self, ifOnInit):
        global win
        win ='ikfkswitchUI_'

        self.ifOn = ifOnInit
        self.arm= []

    def on_keyframe_set(keyframes, client_data):
        print("keyframe set")
        cmds.setKeyframe("RocketGirl_Rig_v1_6:LeftForeArm_FK_CTRL")

    def openSetupWindow(self):
        self.matchingWindow = matchingSetupWindow.matchingSetupWindowUI(self)

    def turnOn(self):
        logger.debug("turn on")
        self.ifOn = True
        self.matchingWindow.close()

        # self.keyframe_callback = OpenMayaAnim.MAnimMessage.addAnimKeyframeEditedCallback(self.on_keyframe_set)
        logger.debug("make callback")

    def turnOff(self):
        self.ifOn= False
        self.matchingWindow.close()


        # OpenMaya.MMessage.removeCallback(self.keyframe_callback)
        logger.debug("delete callback")

    def matchIkFkWin(self):
        fkshldr = self.arm[0]
        fkellbow= self.arm[1]
        fkwrist= self.arm[2]
        ikpv = self.arm[3]
        ikwrist = self.arm[4]
        switchCtrl = self.arm[5]

        #TODO: change to be chosen
        switchAttr= 'IK_FK'

        ikfkMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=1, switchAttrRange=1, rotOffset=[0,0,0], side='L', limb='arm', guessUp=1, bendKneeAxis='+X')

        # pm.select(switchCtrl)

    def matchFkIkWin(self):
        fkshldr = self.arm[0]
        fkellbow= self.arm[1]
        fkwrist= self.arm[2]
        ikpv = self.arm[3]
        ikwrist = self.arm[4]
        switchCtrl = self.arm[5]

        #TODO: change to be chosen
        switchAttr= 'IK_FK'

        fkikMatch(fkwrist, fkellbow, fkshldr, ikwrist, ikpv, switchCtrl, switchAttr, switch0isfk=1, switchAttrRange=1, rotOffset=[0,0,0], side='L', limb='arm')

        # pm.select(switchCtrl)


    def saveIKFkCtrls(self, limb, side, fkshldr, fkellbow, fkwrist, ikpv, ikwrist, switchCtrl, switchAttr, switch0isfk, switchAttrRange, rotOffset, bendKneeAxis):
        '''
        limb = 'arm'/'leg
        side = 'R'/'L'
        '''
        sel = pm.selected()
        ns = fkwrist.split(':')[0] if len(fkwrist.split(':')) > 1 else ''
        storenode = ns + '__' + side + '_' + limb + '_IKFKSTORE'
        logger.info('Storenode is %s'%storenode)
        if pm.objExists(storenode) == False:
            storenode = pm.createNode('transform', n=storenode)
        else:
            message =  'Do you want to replace existing store node?'
            confirm = pm.confirmDialog( title='Replace existing', message=message, button=['Yes','No'],
                              defaultButton='Yes', cancelButton='No', dismissString='No' )
            if confirm == 'Yes':
                logger.info('deleting existing store node')
                pm.delete(storenode)
                storenode = pm.createNode('transform', n=storenode)
            else:
                pm.select(sel)
                return

        storenode = pm.PyNode(storenode)
        storedic = {'fkwrist': fkwrist, 'fkellbow': fkellbow, 'fkshldr':fkshldr, 'ikwrist':ikwrist, 'ikpv':ikpv, 'switchCtrl':switchCtrl, 'switchAttr':switchAttr, 'switch0isfk':switch0isfk, 'attrRange':switchAttrRange, 'rotOffset':rotOffset, 'side':side, 'bendKneeAxis':bendKneeAxis}
        for attrName, value in storedic.items():
            pm.addAttr(storenode, ln=attrName, dt='string', k=1)
            storenode.attr(attrName).set('%s'%value)

        pm.select(sel)
        return storenode

    def loadIkFkCtrl(self, ns, limb, side):
        '''
        limb = 'arm'/'leg
        side = 'R'/'L'
        '''

        storenodeRegex = ns + '__' + side + '_' + limb + '_IKFKSTORE'
        logger.info('loading %s '%storenodeRegex)
        storenode = pm.ls(storenodeRegex)
        if len(storenode) == 0:
            logger.info( 'No storenode found'           )
            return {}
        else:
            storenode = storenode[0]
        ns = storenode.split('__')[0]
        storenode = ns + '__' + side + '_' + limb + '_IKFKSTORE'

        if pm.objExists(storenode) == False:
            return {}
        storenode = pm.PyNode(storenode)

        storedic = {'fkwrist': '', 'fkellbow': '', 'fkshldr':'', 'ikwrist':'', 'ikpv':'', 'switchCtrl':'', 'switchAttr':'', 'switch0isfk':'', 'attrRange':'', 'rotOffset':'', 'bendKneeAxis':'+X'}
        for attrName, value in storedic.items():
            try:
                storedic[attrName] = storenode.attr(attrName).get()
            except:
                pm.warning('Missing Attribute %s. Please Save Store Node again.'%attrName)
                storedic[attrName] = value

        logger.info('StoreNode found is %s'%storedic)
        return storedic



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
    ikwrist_key, ikpv_key = pm.keyframe(ikwrist, q=1, t=pm.currentTime()),\
                                             pm.keyframe(ikpv, q=1, t=pm.currentTime())

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
