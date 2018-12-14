#!/usr/bin/env python
###############################################################################
# Duckietown - Project intnav ETH
# Author: Marta Tintore
# Pure pursuit controller implementation.
###############################################################################
__all__ = [
    'pure_pursuit',
]

import numpy as np
from scipy.spatial.distance import cdist

class Controller(object):
    def __init__(self,direction,path,wheel_distance,
                     adm_error=0.005, la_dis=0.03, min_r=0.07, vel=0.025, n_hist=4):
        '''@param[in]  path            [[x,y],...] target path, numpy array.
        @param[in]  wheel_distance  differential drive vehicle baseline [m].
        @param[in]  adm_error       admissible error (perpendicular distance
                         of future point from the path) [m].
        @param[in]  la_dis          look ahead distance [m].
        @param[in]  min_r           minimal navigation radius [m].
        @param[in]  t_step          time interval to calculate future point [s].
        @param[in]	min_r           minimal turning radius [m].
        @param[in]  vel             output velocity as PP merely controls
                         the steering angle [m/s].'''
        self.direction = direction
        self.path = path
        self.wheel_distance = wheel_distance
        self.adm_error = adm_error
        self.la_dis = la_dis
        self.min_r=0.07
        self.vel=vel
        self.x = 0
        self.y = 0
        self.a = 0 #With x axis (driving direction of the car)
        self.theta_hist = np.zeros((1,n_hist))
        self.right_angle = -np.pi/2 + np.pi/20;
    def pure_pursuit(self,pose):
        ''' Pure pursuit implementation determining control commands (v, tau)
        based on the current pose (x,y,thetha) and an target path.
        @param[in]  pose            (x,y,thetha) current pose [m,rad].'''

        assert len(pose) == 3
        self.x, self.y, self.theta = pose
        self.theta_hist = np.roll(self.theta_hist,1)
        self.theta_hist[0]= self.theta

        #Check if Right angle is reached
        exit = True
        if(self.direction=='R'):
            for i in range(n_hist):
                if(self.theta_hist[i]>self.right_angle):
                    exit=False
        if(exit) return 0,0

        # Predict future point location.
        actual = np.zeros((1,2))
        #future = np.zeros((1,2))
        actual[0,0]=self.x
        actual[0,1]=self.y

        dist_all = cdist(self.path,actual,'euclidean')
        idx_shortest = np.where(dist_all==np.min(dist_all))
        idx_shortest = idx_shortest[0]

        projected_pt = path[idx_shortest[0],:]
        print('projected point', projected_pt)
        distance = 0

        while(distance < self.la_dis and idx_shortest<len(self.path)-1):
            distance += np.linalg.norm(self.path[idx_shortest+1,:]-self.path[idx_shortest,:])
            idx_shortest += 1

        idx_next = idx_shortest
        goal = self.path[idx_next,:]
        print('goalpoint: ', goal)
        # From goal point --> vehicle action (velocity & steering vector).
        sv = (goal[0,0]-actual[0,0],
              goal[0,1]-actual[0,1]) #Steering_vector
        # New orientation for the car.
        ori = np.arctan2(sv[1],sv[0])
        # Compute omega (pure pursuit geometry).
        l = np.linalg.norm(sv)
        al = (np.pi/2) - (ori - self.theta)
        # Complementary of current orientation and desired orientation
        xL = l*np.sin(al)
        yL = l*np.cos(al)
        r = 0.15*(xL**2)/(2*yL) + (yL/2)
        r = np.sign(r)*max(abs(r), min_r)
        tau = vel/r
        print('vl,vr: ', (vel-0.5*tau*wheel_distance),(vel+0.5*tau*wheel_distance))
        return (vel-0.5*tau*wheel_distance),(vel+0.5*tau*wheel_distance)
