#!/usr/bin/env python3
# vim:fenc=utf-8

import rospy
import importlib

def recursive_assign(aClass, aDic):
    for key, value in aDic.items():
        if type(value) == dict:
            key = recursive_assign(getattr(aClass, key), value)
        else:
            setattr(aClass, key, value)
    return aClass

class FlexPub:
    def __init__(self,some_topic_str, msg_pack_str, msg_type_str,):
        mod = importlib.import_module(msg_pack_str)
        self.MsgType = getattr(mod, msg_type_str)
        self.myPub = rospy.Publisher(some_topic_str, self.MsgType, queue_size=1)

    def pub_me(self, msg_contents_dic):
        aMsg = recursive_assign(self.MsgType(), msg_contents_dic)
        #create Publisher

        self.myPub.publish(aMsg)
    
rospy.init_node("gen_pub", anonymous= True)

if True:
    msg_type_list   = rospy.get_param("~msg_type").split("/")
    msg_contents    = rospy.get_param("~msg_contents") ## a dict
    some_topic      = rospy.get_param("~topic")
    wait_time       = rospy.get_param("~delay")

    msg_pack = msg_type_list[0]+".msg"
    msg_type = "".join(msg_type_list[1:])

    myPub = FlexPub(some_topic, msg_pack, msg_type)
    rospy.sleep(wait_time)
    myPub.pub_me(msg_contents)
    rospy.spin()

## unit test of recursive assign
if False:
    i = 0
    myPub = FlexPub("/flexbe/uicommand", "flexbe_msgs.msg", "UICommand")
    while not rospy.is_shutdown():
        i+=1
        myPub.pub_me({"command": "load Acquire_Everything", "key": str(i)})
        rospy.sleep(0.1)

