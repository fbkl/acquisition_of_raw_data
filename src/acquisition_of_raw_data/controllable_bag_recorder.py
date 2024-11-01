#!/usr/bin/env python3
# vim:fenc=utf-8

import rospy
import os
import signal
from std_srvs.srv import Empty, EmptyRequest, EmptyResponse
from opensimrt_msgs.srv import SetFileNameSrv, SetFileNameSrvRequest, SetFileNameSrvResponse
from datetime import datetime

from multiprocessing import Lock
from subprocess import Popen

def get_unique_name(initial_path,ext=".txt"):
    i = 0
    while os.path.exists(initial_path+str(i)+ext):
        i+=1
    return os.path.exists(initial_path+str(i)+ext)

class ControllableNode:
    def __init__(self):
        self.savefile_name = "/tmp/something.txt"
        self.mutex = Lock()
        self.recording = False
        self.savedict_list = []
       
        self.topics = rospy.get_param("~topics_to_read",[])
        if not type(self.topics) == type([]):
            rospy.logfatal_once(f"topics {repr(self.topics)} are incorrectly specified!")
            raise Exception("incorrectly set parameter ~topics_to_read")
        rospy.loginfo(f"recording topics {repr(self.topics)}")

        self.s = rospy.Service('~start_recording', Empty, self.turn_on_recording)
        self.s1 = rospy.Service('~stop_recording', Empty, self.turn_off_recording)
        ## it isnt a sto, but we can use the same names as the saver_node then everything gets easier
        self.s2 = rospy.Service('~write_sto', Empty, self.save)
        self.s3 = rospy.Service('~set_name_and_path', SetFileNameSrv, self.setfilename)
        self.s4 = rospy.Service('~clear', Empty, self.clear)




    def turn_on_recording(self, req):
        with self.mutex:
            rospy.loginfo("Started recording")
            self.recording = True
        return EmptyResponse()

    def turn_off_recording(self, req):
        with self.mutex:
            rospy.loginfo("Stopped recording")
            rospy.loginfo("I save uponstopping, save does nothing.")
            rospy.loginfo("Recorded data saved in %s"%self.savefile_name)
            self.recording = False

        return EmptyResponse()
    
    def save(self, req):
        with self.mutex:
            rospy.logwarn("I save upon stopping, save does nothing.")
        return EmptyResponse()

    def clear(self, req):
        with self.mutex:
            rospy.logwarn("Clear does nothing.")
        return EmptyResponse()

    def setfilename(self, req):
        with self.mutex:
            rospy.loginfo("Using directory for savedata: %s"%req.path)
            rospy.loginfo("Using filename for savedata: %s"%req.name)
            self.savefile_name = req.path + "/" +datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+ req.name + "_bag"
        return SetFileNameSrvResponse()
        

    def run_server(self, ):
        p = None
        while not rospy.is_shutdown(): ## maybe while ros ok
            if self.topics:
                with self.mutex:
                    if self.recording and not p:
                        if not self.savefile_name:
                            rospy.logerr("savefile_name not set!!!!! did you call set_name_and_path?")
                            self.savefile_name = get_unique_name("/tmp/something",ext=".bag")
                            rospy.logwarn(f"file will be saved as {self.savefile_name}")
                        run_args = ["rosbag","record",*self.topics,"-O",self.savefile_name]
                        rospy.loginfo(run_args)
                        p = Popen(run_args)
                    if not self.recording and p:
                        ## transision, i want to kill the process
                        #p.kill()
                        p.send_signal(signal.SIGINT)
                        p = None
            rospy.sleep(0.01)

if __name__ == '__main__':
    rospy.init_node("rosbag_controllable")
    anode = ControllableNode()
    anode.run_server()


