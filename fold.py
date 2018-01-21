#!/usr/bin/env python
"""
External packages ******************************************
"""

import glob
import os
import os.path
import shutil
import socket
import struct
import sys
import time
import subprocess
import warnings
import re
import types
import tarfile
import tempfile

import numpy as np
#import scipy
#import psr_utils
#import presto
#import prepfold

#import sigproc
import math

#import matplotlib
#matplotlib.use('agg') #Use AGG (png) backend to plot
#import matplotlib.pyplot as plt
#import sifting
#import timeit


"""
**************** BINARY PARAMETERS **************************
"""
global P_orb #days
global P_orb_sec
global WD_mass #solar masses
global Min_mass #solar massses

min_pulse_period = 0.001 #sec


def reader(filename):

	"GLOBAL STRINGS: telescope, machine, source_name"
	global telescope
	telescope = subprocess.check_output("header %s -telescope" % (filename), shell=True)
	global machine
	machine = subprocess.check_output("header %s -machine" % (filename), shell=True)
        global source_name

	if (telescope == "Fake\n"):  #if the file is fake we use another source_name because the default is huge and has gaps
		source_name = "Fake"
	else:	
		source_name = subprocess.check_output("header %s -source_name" % (filename), shell=True)

	"GLOBAL FLOATS: fch1, foff, nchans, tstart, tsamp, nbits, nifs, headersize, datasize, nsamples"
	global fch1
	fch1_string = subprocess.check_output("header %s -fch1" % (filename), shell=True)
        fch1 = float(fch1_string)
	global foff
	foff_string = subprocess.check_output("header %s -foff" % (filename), shell=True)
        foff = float(foff_string)
	global nchans
	nchans_string = subprocess.check_output("header %s -nchans" % (filename), shell=True)
        nchans = int(nchans_string)
	global tstart
	tstart_string = subprocess.check_output("header %s -tstart" % (filename), shell=True)
        tstart = float(tstart_string)
	global tsamp
	tsamp_string = subprocess.check_output("header %s -tsamp" % (filename), shell=True)
        tsamp = float(tsamp_string)
	global nbits
	nbits_string = subprocess.check_output("header %s -nbits" % (filename), shell=True)
        nbits = int(nbits_string)
	global nifs 
	nifs_string = subprocess.check_output("header %s -nifs" % (filename), shell=True)
        nifs = int(nifs_string)
	global headersize
	headersize_string = subprocess.check_output("header %s -headersize" % (filename), shell=True)
        headersize = int(headersize_string)
	global datasize
	datasize_string = subprocess.check_output("header %s -datasize" % (filename), shell=True)
        datasize = int(datasize_string)
	global nsamples
	nsamples_string = subprocess.check_output("header %s -nsamples" % (filename), shell=True)
        nsamples = int(nsamples_string)
	global tobs
	tobs_string = subprocess.check_output("header %s -tobs" % (filename), shell=True)
        tobs = float(tobs_string)

def calc(filename):

	"""
	**************** BINARY PARAMETERS **************************
	"""
	global P_orb #days
	global P_orb_sec
	global WD_mass #solar masses
	global Min_mass #solar massses

	P_orb = float(P_orb_str)	#convert sting variables to floats
	WD_mass = float(WD_mass_str)
	Min_mass = float(Min_mass_str)	

	"AC range and step calculation"
	global ACmax
	global ACmin
	global ACstep
	c = 2.99E8               #m/s
        T = 4.925490947E-6       #s in order the masses to be in solar units
        GM = 1.327124400E+11
	P_orb_sec  = P_orb*24*60*60

	Omega_orb = 2*math.pi/(P_orb*24*60*60)
        a_R =((c*T**(1/3))*(Min_mass+WD_mass)**(1/3)) / (Omega_orb**(2/3))
        a_p = a_R*(WD_mass/(Min_mass+WD_mass))
        ACmax = a_p*Omega_orb**2
        ACmin = -a_p*Omega_orb**2

	#ACmax = ((P_orb*24*60*60)**(-4/3))*(GM*(WD_mass + Min_mass)*(2*math.pi)**4)**(1/3) 
	#ACmin = -((P_orb*24*60*60)**(-4/3))*(GM*(WD_mass + Min_mass)*(2*math.pi)**4)**(1/3)

	"Camilo method"
        ACstep = c*min_pulse_period/(tobs**2) 
        "Lyne/Eatough method"
        #ACstep = 64*c*(tsamp*10**(-6))/(tobs**2)

	"AD range and step calculation"
	global ADmax
	global ADmin
	global ADstep
	ADmax = 1
	ADmin = -1
	ADstep = 768*c*(tsamp/1E6)/(tobs**3) #we multiply with 100 because hunt use cm/s^3
	
def fold(filename,resultdir):
	os.chdir(resultdir)
        period = []
        dm = []
	a = []
	pd = []
        qbfile = open("cands.lis","r")
        for i, aline in enumerate(qbfile):
                values = aline.split()
                period.append(float(values[2]))
                dm.append(float(values[3]))
		a.append(float(values[4]))
        qbfile.close()
        numlines = sum(1 for line in open('cands.lis'))
	for i in range (0, numlines): #numlines for the whole file
		p = period[i]/1000
		d = dm[i]
		pd = p*a[i]/300000000 
        	os.system('prepfold -n 64 -nsub 64 -npart 8 -nodmsearch -noxwin -filterbank -p %s -dm %s -pd %s %s -o candi%s' % (p, d, pd, filename, i))
	os.system('convert -adjoin $(ls -1v candi*.ps) candi-s.pdf')
"""**************** MAIN PROGRAM *************************"""

def main(filename):
	reader(filename)
	calc(filename)
	fold(filename,resultdir)

"""*******************************************************"""
if __name__ == "__main__":
	filename = sys.argv[1]
	resultdir = sys.argv[2]
	P_orb_str = sys.argv[3] #days
	WD_mass_str = sys.argv[4] #solar masses
	Min_mass_str = sys.argv[5] #solar masses
	main(filename)
