#!/usr/bin/env python
import shutil
import os
import subprocess
import linecache 

refine3d='Refine3D/job039/run_data.star'
outdir='recon20190424'
postprocess_mask='MaskCreate/job024/mask.mrc'
angpix=0.885
sym='D2'
mtf='mtf_k2_300kV.star'

maxframes=24
if os.path.exists(outdir):
	shutil.rmtree(outdir)

os.makedirs(outdir)

#==============
def updateStarFile(instar,outstar1,outstar2,oldsuffix,newsuffix):
	instaropen=open(instar,'r')
	o1=open(outstar1,'w')
	o2=open(outstar2,'w')
	for line in instaropen:
		if len(line)<40: 
			o1.write(line)
			o2.write(line)
		if len(line)>40: 
			groupnum=line.split()[-1]
			if groupnum == '1':
				newline=line.replace(oldsuffix,newsuffix)
				o1.write(newline)
			if groupnum == '2':
				newline=line.replace(oldsuffix,newsuffix)
				o2.write(newline)
	o1.close()
	o2.close()
	instaropen.close()

#Go through refine3D to re-generate half STAR file sets
currframe=2
while currframe<=maxframes:
	updateStarFile(refine3d,'%s/run_half1_class001_unfil_1_%i.star' %(outdir,currframe),'%s/run_half2_class001_unfil_1_%i.star' %(outdir,currframe),"1_%i"%(maxframes),"1_%i" %(currframe))
	#reconstruct
	submitfile='%s/run_half1_class001_unfil_1_%i_3D_submit.run' %(outdir,currframe)
	o1=open(submitfile,'w')
        o1.write('''#!/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N reconstruct
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=1,pmem=12gb
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=72:00:00
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

# Ensure the necessary modules are loaded
module load gcc/4.9.4
module load openmpi/3.1.2/gcc/4.9.4
module load relion/3.0_beta-cluster/openmpi/3.1.2
module load imod 
# Switch to the working directory
cd $PBS_O_WORKDIR
relion_reconstruct --o %s/run_half1_class001_unfil_1_%i_3D.mrc --i %s/run_half1_class001_unfil_1_%i.star --ctf --sym %s
relion_reconstruct --o %s/run_half2_class001_unfil_1_%i_3D.mrc --i %s/run_half2_class001_unfil_1_%i.star --ctf --sym %s
relion_postprocess --mask %s --i %s/run_half1_class001_unfil_1_%i_3D.mrc --o %s/run_class001_1_%i_3D_postprocess --angpix %f --mtf %s --auto_bfac --autob_lowres 10\n''' %(outdir,currframe,outdir,currframe,sym,outdir,currframe,outdir,currframe,sym,postprocess_mask,outdir,currframe,outdir,currframe,angpix,mtf))
        o1.close()
        cmd='qsub %s' %(submitfile)
        subprocess.Popen(cmd,shell=True).wait()
	currframe=currframe+1


