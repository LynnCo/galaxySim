#custom.py

from __future__ import division
import math
import numpy
import sys

class partitionData (object):
    '''
    Partitions data into 2d or 3d boxes.
    
    [Input]
    data
        type: numpy ndarray
        a collection of the data to be partitioned
    
    [API]
    self.partitionToPoints[partition]
        type: dictionary
        all the points this partition holds
    self.pointToPartition[point]
        type: dictionary
        the partition this point is held in
    self.maxPartition
        type: int
        the number of the last partition
    self.data
        type: numpy ndarray
        you can add new data without reseting the partitions
        this is useful to moving averages
    
    self.partitionAverage[partition]
        type: dictionary
        stores the average for each partition
    self.calculateAverage()
        stores the average of each partition's data into self.partitionAverage

    self.partitionMass[partition]
        type: dictionary
        stores the mass for each partition    
    self.partitionCenterOfMass[partition]
        type: dictionary
        stores the center of mass for each partition
    self.calculateCenterOfMass()
        stores the center of mass in self.partitionCenterOfMass
    '''
    def __init__ (self, data):
        self.data = data
        self.partitionToPoints = dict()
        self.pointToPartition = dict()
        #check input
        assert type(data) is numpy.ndarray, "incorrect data type"
        try:
            sizeX, sizeY, sizeZ = data.shape
            boxSize = math.floor(((sizeX+sizeY+sizeZ)/3)**0.5)
            for (x, y, z), v in numpy.ndenumerate(data):
                boxX = x//boxSize
                boxY = y//boxSize
                boxZ = z//boxSize
                box = boxX+boxSize*boxY+(boxSize**2)*boxZ
                self.pointToPartition[(x,y,z)] = box
                try:
                    self.partitionToPoints[box].append((x,y,z))
                except KeyError:
                    self.partitionToPoints[box] = list()
                    self.partitionToPoints[box].append((x,y,z))
        except ValueError:
            sizeX, sizeY = data.shape
            boxSize = math.floor(((sizeX+sizeY)/2)**0.5)
            for (x, y), v in numpy.ndenumerate(data):
                boxX = x//boxSize
                boxY = y//boxSize
                box = boxX+boxSize*boxY
                self.pointToPartition[(x,y)] = box
                try:
                    self.partitionToPoints[box].append((x,y))
                except KeyError:
                    self.partitionToPoints[box] = list()
                    self.partitionToPoints[box].append((x,y))
        inBox = 0
        for k, v in self.partitionToPoints.items(): 
            inBox += len(v)
        #checks for some sort of obscure error
        assert inBox == data.size, "all data not placed in boxes"
        self.maxPartition = len(self.partitionToPoints)-1
        print(str(len(self.pointToPartition))+" data points -> "+str(len(self.partitionToPoints))+" partitions")

    def calculateAvereage (self, param=0):
        '''
        given a data set where data[i] = value, averages that value

        but if given a param, calculates the average of data[i][param]
        '''
        self.partitionAverage = dict()
        for partition, points in self.partitionToPoints.items():
            valueSum = 0
            locationSum = [0,0]
            numPoints = len(points)
            for point in points:
                if not param:
                    valueSum += self.data[point]
                elif param == "index":
                    locationSum[0] += point[0]
                    locationSum[1] += point[1] 
                else:
                    valueSum += self.data[point][param]
            if param == "index":
                self.partitionAverage[partition] = (locationSum[0]/numPoints,locationSum[1]/numPoints)
            else:
                self.partitionAverage[partition] = valueSum/numPoints

    def calculateCenterOfMass (self):
        '''
        assumes the input data set is of format data[i] = mass
        '''
        self.partitionCenterOfMass = dict()
        self.partitionMass = dict()
        for partition, points in self.partitionToPoints.items():
            weightedPostition = [0,0]
            totalMass = 0
            for point in points:
                mass = self.data[point]
                totalMass += mass
                weightedPostition[0] += mass*point[0]
                weightedPostition[1] += mass*point[1]
            COM = [weightedPostition[0]/totalMass, weightedPostition[1]/totalMass]
            self.partitionCenterOfMass[partition] = COM
            self.partitionMass[partition] = totalMass

class loopProgress (object):
    '''
    simple two line loop progress indicator

    [Example]
    pb = loopProgress(100-1) #initilize indicator
    for i in range(100):
        pb.update(i) #update value
    '''
    def __init__ (self, maxVal=0):
        self.maxVal = maxVal-1
        print("Loop progress")
    def update (self, counter):
        sys.stdout.flush()
        if self.maxVal:
            sys.stdout.write("\r{}/{}".format(counter,self.maxVal))
        else:
            sys.stdout.write("\r{}".format(counter))


def rotate (point_x, point_y, rads, center=(0,0)):
    newX = center[0] + (point_x-center[0])*math.cos(rads) - (point_y-center[1])*math.sin(rads)
    newY = center[1] + (point_x-center[0])*math.sin(rads) + (point_y-center[1])*math.cos(rads)
    return newX,newY

def build_distance_matrix (size):
    distance_matrix = dict()
    known_distances = dict()
    pb = loopProgress(size)
    for x1 in range(size):
        for y1 in range(size):
            distance_matrix[x1, y1] = numpy.empty((size, size))
            for (x2, y2), dont_need in numpy.ndenumerate(distance_matrix[x1, y1]):
                dx, dy = abs(x1-x2), abs(y1-x2)
                if (dx,dy) in known_distances.keys():
                    distance_matrix[x1, y1][x2, y2] = known_distances[dx,dy]
                else:
                    dist =  math.hypot(dx, dy)
                    known_distances[dx,dy] = dist
                    known_distances[dy,dx] = dist
                    distance_matrix[x1, y1][x2, y2] = dist
                distance_matrix[x1, y1][x2, y2] = math.hypot(dx, dy)
        pb.update(x1)
    return distance_matrix

def sortkeys (data):
    out = list()
    for entry in data.keys(): out.append(entry)
    return sorted(out)

def make_sphere (r): 
    inr = set()
    for x in range(r+1):
        for y in range(r+1):
            if math.hypot(x,y)<=r:
                inr.add((x,y))
                inr.add((-x,y))
                inr.add((x,-y))
                inr.add((-x,-y))
    dmap = dict()
    for x,y in inr:
        dmod = r+1-math.hypot(x,y)
        dmap[x,y] = dmod
    return dmap