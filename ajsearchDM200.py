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
import math
import sigpyproc 

#for downsampling 
from sigpyproc.Readers import FilReader
#for conversion from .dat to .tim
from sigpyproc.Readers import readDat
"""
**************** SEARCH PARAMETERS **************************
"""
min_pulse_period = 0.001 #sec  (for Camillo method)

"DEDISPERSION"
dmlistpath = "/u/tilemath/bin/pipeline2017/DMlists/dmlist200.txt"

"""
*************************************************************
"""
dmlist = []
dm = []

def reader(filename, workdir):
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
	
#	os.chdir(workdir)
	#READ THE DMLIST
#	qbfile = open("dmlist","r")
#	for i, aline in enumerate(qbfile):
#		values = aline.split()
#		dm.append(values[0])
#	qbfile.close()


def calc(filename, P_orb_str, WD_mass_str, Min_mass_str):
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
        GM = 1.327124400E+20
	P_orb_sec  = P_orb*24*60*60
	
	Omega_orb = 2*math.pi/(P_orb_sec)
	a_R =(c*(T*(Min_mass+WD_mass))**(0.333333333))/Omega_orb**0.666666667
	a_p = a_R*(WD_mass/(Min_mass+WD_mass))
	a=a_p*Omega_orb**2

        ACmax = a_p*Omega_orb**2
        ACmin = -a_p*Omega_orb**2

	"Camilo method"
        #ACstep = c*min_pulse_period/(tobs**2) 
        "Lyne/Eatough method"
        ACstep = 64*c*(tsamp*10**(-6))/(tobs**2)
	
	global ADmax
	global ADmin
	global ADstep
	
	omegadot=3*T**(0.66666666)*(WD_mass+Min_mass)**(0.66666666)*Omega_orb**(1.66666666)
	ADmax=ACmax*omegadot
	ADmin=-ACmax*omegadot
	ADstep=ADmax/4
	#ADstep = 768*c*(tsamp*10**(-6))/(tobs**3)

	os.system('step %s %s %s > aclist' % (ACmin, ACmax, ACstep))
	os.system('step %s %s %s > adlist' % (ADmin, ADmax, ADstep))

def downsamp(filename, workdir):
	os.chdir(workdir)
        print("Downsampling")
        original = FilReader("%s" % filename)
        original.downsample(2, 1, 512, None, True)
        original.downsample(4, 1, 512, None, True)

def DM(filename, workdir):
	print "Dedispersion, zerodming, bad channels"
	os.system('dedisperse_trials -f %s -d 0:49 -o DM' % filename) #-c for badchannels 
	os.system('dedisperse_trials -f %s_f1_t2 -d 49:147 -z -t 120 -o DM' % filename)
	os.system('dedisperse_trials -f %s_f1_t4 -d 147:200 -z -o DM' % filename)

def DMprepdata(filename, filename2, filename4, P_orb_str, WD_mass_str, Min_mass_str, workdir):
        os.chdir(workdir)
	print("RFI find")
	os.system('rfifind -time 2.0 -o rfi %s' % filename)
        global dmlist
        global dm
        dedmea = open(dmlistpath, "r")
        effdmlist = dedmea.readlines
        i=0
        for item in dedmea:
                dmi = float(item)
                dmlist.append(dmi)
		if i<=195:			
			#reader(filename, workdir)
			#calc(filename, P_orb_str, WD_mass_str, Min_mass_str)
			os.system('prepdata -nobary -zerodm -o DM_%s -dm %s -mask rfi_rfifind.mask -numout 530000 %s' % (str(dmlist[i]), str(dmlist[i]), filename))#-subzero
			datfile=readDat("DM_%s.dat" % str(dmlist[i]) , "DM_%s.inf" % str(dmlist[i]))
			datfile.toFile("DM_%s.tim" % str(dmlist[i]))
			os.system('rm -rf DM_%s.dat' % str(dmlist[i]))
			os.system('rm -rf DM_%s.inf' % str(dmlist[i]))
			os.system('my_accn DM_%s' % str(dmlist[i]))
			print(i)
		elif (i>195 and i<=400):
			#reader(filename2, workdir)
			#calc(filename2, P_orb_str, WD_mass_str, Min_mass_str)
			os.system('prepdata -nobary -zerodm -o DM_%s -dm %s -mask rfi_rfifind.mask -numout 530000 %s' % (str(dmlist[i]), str(dmlist[i]), filename2))#-subzero
			datfile=readDat("DM_%s.dat" % str(dmlist[i]) , "DM_%s.inf" % str(dmlist[i]))
			datfile.toFile("DM_%s.tim" % str(dmlist[i]))
			os.system('rm -rf DM_%s.dat' % str(dmlist[i]))
			os.system('rm -rf DM_%s.inf' % str(dmlist[i]))
			os.system('my_accn DM_%s' % str(dmlist[i]))
		else:
			#reader(filename4, workdir)
			#calc(filename4, P_orb_str, WD_mass_str, Min_mass_str)
			os.system('prepdata -nobary -zerodm -o DM_%s -dm %s -mask rfi_rfifind.mask -numout 530000 %s' % (str(dmlist[i]), str(dmlist[i]), filename4))#-subzero
			datfile=readDat("DM_%s.dat" % str(dmlist[i]) , "DM_%s.inf" % str(dmlist[i]))
			datfile.toFile("DM_%s.tim" % str(dmlist[i]))
			os.system('rm -rf DM_%s.dat' % str(dmlist[i]))
			os.system('rm -rf DM_%s.inf' % str(dmlist[i]))
			os.system('my_accn DM_%s' % str(dmlist[i]))
			#os.system('rm -rf aclist')
			#os.system('rm -rf adlist')
			#open(aclist, 'w').close()
			#open(adlist, 'w').close()
                i=i+1
        dedmea.close()
	
def search(workdir, mode):
	os.chdir(workdir)
	if mode==0:
		for i in range (0, 195):
			print "Searching..."
			os.system('my_accn DM_%s' % str(dmlist[i])) 
			i=i+1
	elif mode==2:
		for i in range (195,400):
			print "Searching..."
                        os.system('my_accn DM_%s' % str(dmlist[i]))
                        i=i+1
	else:
		for i in range (400, 453):
			print "Searching..."
                        os.system('my_accn DM_%s' % str(dmlist[i]))
                        i=i+1
	os.system('cat aclist adlist > list%s' % mode)   #for inspection 
	os.system('rm -rf aclist') #remove so they can be updated correctly
        os.system('rm -rf adlist')

def conclude(workdir):
	os.chdir(workdir)
	os.system('cat DM_*.prd > all.prd')
	os.system('cp %s/all.prd %s/all.prd' % (workdir, resultdir) )
	os.chdir(resultdir)
	print "Finding best candidates..."
	os.system('condense_try.py -f all.prd -s 10')
        os.system('/hercules/u/tilemath/bin/pipeline2017/pulsarhunter/scripts/ph-best all.prd.condensed-SN10.prd cands')
	print "Procedure Completed."

"""**************** MAIN PROGRAM *************************"""

def main(workdir, resultdir, filename):

	filename_full=filename+".fil"
	filename2=filename+"_f1_t2"
	filename2_full=filename2+".fil"
	filename4=filename+"_f1_t4"
	filename4_full=filename4+".fil"

	downsamp(filename_full, workdir)

	reader(filename_full, workdir)
	calc(filename_full, P_orb_str, WD_mass_str, Min_mass_str)
	DMprepdata(filename_full, filename2_full, filename4_full, P_orb_str, WD_mass_str, Min_mass_str, workdir)
	conclude(workdir)
	print "Search completed."

"""*******************************************************"""
if __name__ == "__main__":
	workdir = sys.argv[1]
   	resultdir = sys.argv[2]
	filename = sys.argv[3]
	P_orb_str = sys.argv[4] #days
	WD_mass_str = sys.argv[5] #solar masses
	Min_mass_str = sys.argv[6] #solar masses
	main(workdir, resultdir, filename)
