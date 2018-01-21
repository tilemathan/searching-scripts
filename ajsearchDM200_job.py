#!/usr/bin/env python
import os
import sys

def create_shfiles(sourcename, P_orb, WD_mass, Min_mass):
	os.chdir('/hercules/u/tilemath/PILOT-SURVEY-DATA/%s/' % (sourcename))
	for beam in range (0, 1):
		beamstr = str(beam)
		os.system("mkdir %s-workdir%s" % (sourcename,beam))
		os.system("cp birdies_%s %s-workdir%s/birdies" % (sourcename, sourcename,beam))
		os.system("mkdir /hercules/u/tilemath/PILOT-SURVEY-RESULTS/ACAJ/%s-results%s" % (sourcename, beam))
		os.system("mkdir %s-job%s" % (sourcename,beam))
		os.chdir("%s-job%s" % (sourcename,beam))
		f = open(sourcename+"_0"+beamstr+".sh", "w")
		f.write("#!/bin/bash -l"+'\n')
		f.write("# Standard output and error:"+'\n')
		f.write("#SBATCH -o ./"+sourcename+"_out.%j"+'\n')
		f.write("#SBATCH -e ./"+sourcename+"_err.%j"+'\n')
		f.write("# Initial working directory:"+'\n')
		f.write("#SBATCH -D ./"+'\n')
		f.write("# Job Name:"+'\n')
		f.write("#SBATCH -J"+" "+sourcename+"_"+beamstr+'\n')
		f.write("# Queue (Partition):"+'\n')
		f.write("#SBATCH --partition=long.q"+'\n')
		f.write("# Number of nodes and MPI tasks per node:"+'\n')
		f.write("#SBATCH --nodes=1"+'\n')
		f.write("#SBATCH --ntasks-per-node=24"+'\n')
		f.write("#"+'\n')
		f.write("#SBATCH --mail-type=all"+'\n')
		f.write("#SBATCH --mail-user=<tilemathan@mpifr.de>"+'\n')
		f.write("#SBATCH --mem=30700"+'\n')
		f.write("#"+'\n')
		f.write("module load impi"+'\n')
		f.write("module load sigproc"+'\n')
		f.write("module load presto"+'\n')
		f.write("module load mkl"+'\n')
		f.write("module load intel/17.0"+'\n')
		f.write("module load minuit"+'\n')
		f.write("module load cfitsio"+'\n')
		f.write("module load anaconda"+'\n')
		f.write("module load git"+'\n')
		f.write("module load gsl"+'\n')
		f.write("module load imagemagick"+'\n')
		f.write("# Run the program:"+'\n')
		f.write("srun ajsearchDM200.py /hercules/u/tilemath/PILOT-SURVEY-DATA/"+sourcename+"/"+sourcename+"-"+"workdir"+beamstr+" /hercules/u/tilemath/PILOT-SURVEY-RESULTS/ACAJ/"+sourcename+"-"+"results"+beamstr+" /hercules/u/tilemath/PILOT-SURVEY-DATA/"+sourcename+"/"+sourcename+"_"+"0"+beamstr+"_8bit"+" "+P_orb+" "+WD_mass+" "+Min_mass)
		f.close()
		os.system("chmod +x"+" "+sourcename+"_0"+beamstr+".sh")
		os.system("sbatch %s_0%s.sh" % (sourcename, beamstr))
		os.chdir("..")
	os.chdir('/hercules/u/tilemath/PILOT-SURVEY-DATA/%s/' % sourcename)

if __name__ == "__main__":
	sourcename = sys.argv[1]
	P_orb = sys.argv[2]
	WD_mass = sys.argv[3]
	Min_mass = sys.argv[4]	
	create_shfiles(sourcename, P_orb, WD_mass, Min_mass)
