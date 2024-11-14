#!/usr/bin/env python3
# vim:fenc=utf-8

#
# @author      : frekle (frekle@bml01.mech.kth.se)
# @file        : multiservice_plex
# @created     : Monday Apr 22, 2024 10:42:19 CEST
#


import rospy
from std_srvs.srv import Empty, EmptyRequest, EmptyResponse

from concurrent.futures import ThreadPoolExecutor


# from https://gist.github.com/jbohren/e33247f7675b5dab05543637098a538b
class AsyncWaitingServiceProxy(object):
    """Asynchronous ROS service proxy

    Example 1:

        add_two_ints_async = AsyncServiceProxy('add_two_ints',AddTwoInts)
        fut = add_two_ints_async(1, 2)
        while not fut.done():
            print('Waiting...')
        try:
            print('Result: {}'.format(fut.result()))
        except ServiceException:
            print('Service failed!')

    Example 2:
        def result_cb(fut):
            try:
                print('Result: {}'.format(fut.result()))
            except ServiceException:
                print('Service failed!')

        add_two_ints_async = AsyncServiceProxy('add_two_ints',AddTwoInts,callback=result_cb)
        fut = add_two_ints_async(1, 2)
        while not fut.done():
            print('Waiting...')
    """
    def complete_call(self):
        rospy.wait_for_service(self.service_name)
        self.service_proxy.call()

    def __init__(self, service_name, service_type, persistent=True,
            headers=None, callback=None):
        """Create an asynchronous service proxy."""

        self.service_name =  service_name
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.service_proxy = rospy.ServiceProxy(
                service_name,
                service_type,
                persistent,
                headers)

        self.callback = callback

    def __call__(self, *args, **kwargs):
        """Get a Future corresponding to a call of this service."""

        fut = self.executor.submit(self.complete_call, *args, **kwargs)
        if self.callback is not None:
            fut.add_done_callback(self.callback)

        return fut


class WaitingMultiServiceCaller:
    """WaitingMultiServiceCaller

        Calls multiple services in parallel (non-blocking)
        
    """
    def __init__(self, list_services_, srvMsgType = Empty(), srvMsgTypeResponse = EmptyResponse(), wait_to_start=True, wait_for_responses = False, timeout = rospy.Duration(1)):
        rospy.logwarn_once("this can be quite slow. also maybe the services are blocking, ..")
        self.list_of_services = {}
        self.error_list =[]
        self.wait_for_responses = wait_for_responses ## if set to true, it is very slow
        self.response = srvMsgTypeResponse
        for a_srv_name in list_services_:
            self.list_of_services.update({a_srv_name:AsyncWaitingServiceProxy(a_srv_name, srvMsgType )})
    def __call__(self, srvMsg):
        response_list = []
        self.error_list =[]

        for a_srv_name, a_srv in self.list_of_services.items():
            try:
                rospy.loginfo(f"calling service {a_srv_name} with msg:\n==\n{srvMsg}\n==\n")
                a_response = a_srv(srvMsg)
                if self.wait_for_responses:
                    response_list.append(a_response.result())
                else:
                    response_list.append(a_response)
            except rospy.ServiceException as e:
                rospy.logerr(f"failed to call srv {a_srv_name}")
                self.error_list.append(a_srv_name+"error: %s"%e)
        rospy.loginfo("done.")
        # return response_list
        return self.response, response_list

def main():
    rospy.init_node("ms")
    aMulti = WaitingMultiServiceCaller(
            ["/ximu_torso/start_now",
                "/ximu_pelvis/start_now",
                "/ximu_femur_l/start_now",
                "/ximu_femur_r/start_now",
                "/ximu_tibia_l/start_now",
                "/ximu_tibia_r/start_now",
                "/ximu_talus_l/start_now",
                "/ximu_talus_r/start_now",
                ]
            )


    rospy.Service("~start_imus",Empty,lambda req: aMulti(EmptyRequest())[0])
    #    aMulti(EmptyRequest())
    rospy.spin()

if __name__ == '__main__':
    main()



